# -*- coding: utf-8 -*-
"""Briot-Ruffini, deflação e raízes múltiplas: extrair todas as raízes.

O QUE RESOLVE
    1. Avalia p e p' numa única passada (Horner duplo) e confere contra
       np.polyval e np.polyder.
    2. Deflaciona por Briot-Ruffini e verifica que o resto é nulo.
    3. Mostra que Newton perto de uma raiz simples termina num ciclo de
       dois valores, e constrói um teste de parada que sobrevive a isso.
    4. Extrai todas as raízes ligando o isolamento da aula 7 à deflação,
       e mede o que a ordem da deflação e o polimento realmente valem.
    5. Diagnostica a multiplicidade pela razão dos incrementos e mede o
       limite de precisão eps^(1/m).
    6. Reproduz o polinômio de Wilkinson e confere o deslocamento das
       raízes contra o número de condição, previsto coeficiente a
       coeficiente.
    7. Acha o par complexo por Bairstow, com aritmética real do começo
       ao fim.
    8. Resolve os modos normais de três massas acopladas por este
       caminho, e compara com a rota matricial.

A IDEIA
    A aula 7 terminou com as raizes isoladas, uma por intervalo. Falta
    refinar cada uma e seguir adiante. O instrumento e sempre o mesmo
    esquema de Horner, usado de tres maneiras.

    Primeiro, para avaliar p e p' de uma vez: a recorrencia de Horner
    aplicada duas vezes da o valor e a derivada com cerca de 2n
    multiplicacoes, o que torna Newton barato.

    Segundo, para deflacionar: os coeficientes intermediarios de Horner
    sao o quociente da divisao por (x - r). Achada uma raiz, o problema
    perde um grau, e o grau 1 se resolve de cabeca.

    Terceiro, para diagnosticar. Numa raiz de multiplicidade m, Newton
    deixa de convergir quadraticamente e passa a reduzir o erro por um
    fator constante (m-1)/m. Essa razao, que o programa mede, denuncia a
    multiplicidade sem que ninguem precise fatorar nada.

    O preco de tudo isso aparece no fim. Os coeficientes de um polinomio
    sao uma representacao numericamente fragil das raizes, e Wilkinson
    mostrou o quanto: mexer na decima-sexta casa de um coeficiente move
    raizes em unidades. Saber quando NAO usar polinomios e parte do que
    esta aula ensina.

COMO CONFERIR SE ESTA CERTO
    1. Horner duplo e comparado com np.polyval e np.polyval(np.polyder)
       em quatro pontos.
    2. Todo resto de deflacao em raiz exata tem de ser nulo, e o
       programa imprime os restos.
    3. O ciclo de Newton e exibido iteracao por iteracao, e sua
       amplitude e comparada com |p calculado| / |p'|.
    4. A comparacao entre ordens de deflacao e entre polir e nao polir e
       feita em 300 polinomios aleatorios, nao em um exemplo escolhido.
    5. O L medido e comparado com (m-1)/m para m = 1, 2, 3 e 4, e o erro
       final com eps^(1/m).
    6. O deslocamento das raizes de Wilkinson e comparado com a previsao
       |x^k / p'(x)| do numero de condicao, e o grau 20 e mostrado como
       um experimento que o float64 nao consegue sequer montar.
    7. Bairstow reproduz o exemplo do livro em 25 iteracoes, e o par
       encontrado depende do palpite, o que o programa exibe.
    8. Os autovalores das tres massas sao conferidos contra
       np.linalg.eigvalsh e contra a solucao fechada 4 sen^2(j pi / 2(N+1)).

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import numpy as np

EPS = np.finfo(float).eps

# o polinomio que acompanha as aulas 7 e 8: raizes -2, -1, 1, 2, 3
P = [1.0, -3.0, -5.0, 15.0, 4.0, -12.0]
RAIZES_P = [-2.0, -1.0, 1.0, 2.0, 3.0]


# ---------------------------------------------------------------- 1
def horner2(coefs, x):
    """p(x) e p'(x) numa unica passada.

    Os coeficientes vem em grau decrescente, como em np.polyval.
    """
    b = coefs[0]
    d = coefs[0]
    for a in coefs[1:-1]:
        b = a + b * x
        d = b + d * x
    b = coefs[-1] + b * x
    return b, d


def briot_ruffini(coefs, r):
    """Divide p por (x - r). Devolve o quociente e o resto."""
    b = [coefs[0]]
    for a in coefs[1:-1]:
        b.append(a + b[-1] * r)
    resto = coefs[-1] + b[-1] * r
    return b, resto


def cota_cauchy(coefs):
    """Toda raiz tem modulo menor que esta cota (aula 7)."""
    return 1.0 + max(abs(a / coefs[0]) for a in coefs[1:])


# ---------------------------------------------------------------- 3
def newton_pol(coefs, x0, nmax=200, multiplicidade=1, historico=False):
    """Newton com Horner duplo, com parada que sobrevive ao ciclo final.

    Perto de uma raiz simples, em float64, Newton nao converge: entra
    num ciclo de dois ou tres valores vizinhos, de amplitude
    |p calculado| / |p'|. Um teste do tipo |dx| < tol * |x| pode nunca
    disparar. Por isso guardamos o melhor ponto visto, medido por |p|, e
    paramos quando |p| para de melhorar E o passo ja e pequeno.
    """
    x = float(x0)
    melhor, pmelhor = x, abs(horner2(coefs, x)[0])
    hist = [x]
    k = 0
    for k in range(nmax):
        v, d = horner2(coefs, x)
        if d == 0.0:
            break
        dx = -multiplicidade * v / d
        if x + dx == x:          # o passo e menor que meio ulp
            break
        x = x + dx
        if historico:
            hist.append(x)
        pv = abs(horner2(coefs, x)[0])
        if pv < pmelhor:
            melhor, pmelhor = x, pv
        elif abs(dx) < 1e-8 * max(1.0, abs(x)):
            break                # ja estamos no chao do arredondamento
    return (melhor, k + 1, hist) if historico else (melhor, k + 1)


# ---------------------------------------------------------------- 4
def extrair_raizes(coefs, chutes, polir=True):
    """Extrai todas as raizes reais por deflacao sucessiva.

    chutes vem na ordem em que as raizes serao extraidas. Com polir, cada
    raiz encontrada no polinomio deflacionado e refinada no polinomio
    ORIGINAL antes de deflacionar.
    """
    original = list(coefs)
    c = list(coefs)
    raizes, restos = [], []
    for chute in chutes[:-1]:
        r, _ = newton_pol(c, chute)
        if polir:
            r, _ = newton_pol(original, r)
        q, resto = briot_ruffini(c, r)
        raizes.append(r)
        restos.append(resto)
        c = q
    r = -c[1] / c[0]                      # o grau 1 que sobra
    if polir:
        r, _ = newton_pol(original, r)
    raizes.append(r)
    return raizes, restos


# ---------------------------------------------------------------- 6
def diagnostico(coefs, x0, piso=1e-7):
    """Estima a multiplicidade pela razao dos incrementos de Newton.

    Numa raiz de multiplicidade m, dx_{k+1} / dx_k tende a (m-1)/m. Os
    passos abaixo do piso ja sao ruido e nao entram na conta.
    """
    x = float(x0)
    passos = []
    for _ in range(400):
        v, d = horner2(coefs, x)
        if d == 0.0:
            break
        dx = -v / d
        if x + dx == x:
            break
        x = x + dx
        passos.append(dx)
    limpos = [p for p in passos if abs(p) > piso]
    if len(limpos) < 4:
        return 0.0, 1, x, len(passos)     # convergiu rapido: raiz simples
    razoes = [abs(limpos[i + 1] / limpos[i]) for i in range(len(limpos) - 1)]
    L = float(np.median(razoes[len(razoes) // 3:]))
    m = int(round(1.0 / (1.0 - L))) if L < 0.95 else 0
    return L, m, x, len(passos)


# ---------------------------------------------------------------- 8
def bairstow(coefs, u, v, tol=1e-14, nmax=300):
    """Extrai um fator quadratico x^2 - u x - v, so com aritmetica real."""
    c = [float(a) for a in coefs]
    n = len(c) - 1
    for it in range(nmax):
        b = [0.0] * (n + 1)
        f = [0.0] * (n + 1)
        b[0] = c[0]
        b[1] = c[1] + u * b[0]
        for i in range(2, n + 1):
            b[i] = c[i] + u * b[i - 1] + v * b[i - 2]
        f[0] = b[0]
        f[1] = b[1] + u * f[0]
        for i in range(2, n):
            f[i] = b[i] + u * f[i - 1] + v * f[i - 2]
        c1, c2 = b[n - 1], b[n]
        det = f[n - 2] ** 2 - f[n - 3] * f[n - 1]
        if det == 0.0:
            return None
        du = (-c1 * f[n - 2] + c2 * f[n - 3]) / det
        dv = (-c2 * f[n - 2] + c1 * f[n - 1]) / det
        u, v = u + du, v + dv
        if abs(du) + abs(dv) < tol:
            return u, v, b[:n - 1], it + 1
    return None


def main():
    print()
    print('=' * 68)
    print('  BRIOT-RUFFINI, DEFLACAO E RAIZES MULTIPLAS')
    print('=' * 68)
    print()

    # ---------------------------------------------------------------- 1
    print('1. HORNER DUPLO: p E p\' NUMA PASSADA')
    print()
    print('   p(x) = x^5 - 3x^4 - 5x^3 + 15x^2 + 4x - 12, raizes -2 -1 1 2 3')
    print()
    print('   A mesma recorrencia de Horner, aplicada duas vezes, da o valor')
    print('   e a derivada. Sao cerca de 2n multiplicacoes, contra n para')
    print('   cada forma ingenua mais as potencias.')
    print()
    dP = np.polyder(P)
    print('        x       p (nosso)      p (numpy)     p\' (nosso)    p\' (numpy)')
    for x in (2.0, 1.5, -1.0, 3.0):
        v, d = horner2(P, x)
        print('     %5.1f   %12.6f  %12.6f   %12.6f  %12.6f'
              % (x, v, np.polyval(P, x), d, np.polyval(dP, x)))
        assert abs(v - np.polyval(P, x)) < 1e-12
        assert abs(d - np.polyval(dP, x)) < 1e-12
    print()
    print('   Concordam em todas as casas, nos quatro pontos.')
    print()

    # ---------------------------------------------------------------- 2
    print('2. BRIOT-RUFFINI: O QUOCIENTE E O RESTO')
    print()
    print('   Os coeficientes intermediarios de Horner SAO o quociente da')
    print('   divisao por (x - r). Se r e raiz, o resto tem de ser nulo.')
    print()
    for r in (2.0, 1.0, 1.5):
        q, resto = briot_ruffini(P, r)
        eh = 'raiz' if abs(np.polyval(P, r)) < 1e-12 else 'nao e raiz'
        print('     r = %4.1f (%10s): quociente %s' % (r, eh, ' '.join('%g' % a for a in q)))
        print('                            resto %+.3e' % resto)
    print()
    q2, _ = briot_ruffini(P, 2.0)
    volta = np.polyadd(np.polymul([1.0, -2.0], q2), [0.0])
    print('   Conferindo: (x - 2) * quociente = %s' % ' '.join('%g' % a for a in volta))
    print('   e o polinomio original era       %s' % ' '.join('%g' % a for a in P))
    assert np.allclose(volta, P)
    print('   Identicos (np.allclose).')
    print()

    # ---------------------------------------------------------------- 3
    print('3. O CICLO FINAL DE NEWTON, E O TESTE DE PARADA')
    print()
    print('   Esta e a armadilha mais discreta da aula. Tome o polinomio')
    print('   (x-1)(x-2)...(x-8), expandido, e rode Newton perto de x = 1.')
    print()
    W8 = list(np.poly(np.arange(1, 9)))
    x = 0.90122222900390625
    print('      k      x                      p(x) calculado      dx')
    ciclo = []
    for k in range(9):
        v, d = horner2(W8, x)
        dx = -v / d
        print('     %2d   %.17f   %+.6e   %+.3e' % (k, x, v, dx))
        if k >= 6:
            ciclo.append((abs(v), abs(dx)))
        if x + dx == x:
            break
        x = x + dx
    print()
    print('   A partir de k = 6 a iteracao ENTRA EM CICLO: alterna entre dois')
    print('   vizinhos de 1, com p calculado trocando de sinal. Nenhum dos')
    print('   dois e melhor que o outro, e um teste |dx| < 1e-15 |x| nunca')
    print('   dispara, porque a amplitude do ciclo nao e um ulp:')
    print()
    pciclo = ciclo[0][0]
    dp1 = np.polyval(np.polyder(W8), 1.0)
    print('      |p calculado| no ciclo        %.3e' % pciclo)
    print('      |p\'(1)|                       %.0f' % abs(dp1))
    print('      amplitude prevista = |p| / |p\'|   %.2e' % abs(pciclo / dp1))
    print('      amplitude medida no ciclo         %.2e' % ciclo[0][1])
    assert abs(ciclo[0][1] - abs(pciclo / dp1)) < 1e-17
    print()
    print('   O chao de |p| e no maximo o arredondamento da propria soma de')
    print('   Horner, eps * soma|a_i| = %.1e (a soma dos modulos aqui e'
          % (EPS * float(np.sum(np.abs(W8)))))
    print('   9! = %d). O medido, %.2e, fica abaixo desse limite.'
          % (int(np.sum(np.abs(W8))), pciclo))
    print()
    print('   Dai o teste de parada de newton_pol: guarda o melhor ponto')
    print('   visto, medido por |p|, e para quando |p| para de melhorar E o')
    print('   passo ja e pequeno. Sem a segunda condicao ele para cedo, no')
    print('   meio da aproximacao, e deflaciona uma raiz errada.')
    print()

    # ---------------------------------------------------------------- 4
    print('4. EXTRACAO COMPLETA: A AULA 7 LIGADA A DEFLACAO')
    print()
    try:
        from polinomios import isolar
        R = cota_cauchy(P)
        intervalos = isolar(P, -R, R)
        chutes = sorted(0.5 * (a + b) for a, b in intervalos)
        print('   O Sturm da aula 7 isolou %d intervalos dentro da cota de'
              % len(intervalos))
        print('   Cauchy (%.0f), e os pontos medios sao os chutes.' % R)
    except ImportError:
        chutes = [-2.2, -0.8, 1.2, 1.8, 3.3]
        print('   (polinomios.py nao esta nesta pasta; usando chutes fixos)')
    print()
    raizes, restos = extrair_raizes(P, chutes, polir=True)
    print('      raiz extraida        erro          resto da deflacao')
    for r, resto in zip(raizes, restos + [0.0]):
        exata = min(RAIZES_P, key=lambda v: abs(v - r))
        print('      %+.15f   %.2e      %+.2e' % (r, abs(r - exata), resto))
    erro = max(abs(r - min(RAIZES_P, key=lambda v: abs(v - r))) for r in raizes)
    assert erro < 1e-13
    print()
    print('   Maior erro %.2e, e todos os restos nulos.' % erro)
    print()
    print('   E a cota de Cauchy como ponto de partida? Ela delimita bem, mas')
    print('   e um lugar pessimo para COMECAR: longe de todas as raizes o')
    print('   passo de Newton vale so x/n, de modo que x cai por um fator')
    print('   (1 - 1/n) por iteracao.')
    print()
    print('      grau   cota de Cauchy   passos de Newton partindo dela')
    for n in (5, 8, 10):
        Wn = list(np.poly(np.arange(1, n + 1)))
        Rn = cota_cauchy(Wn)
        _, k = newton_pol(Wn, Rn, nmax=2000)
        print('      %4d   %13.3g   %d' % (n, Rn, k))
    print()
    print('   Delimitar e comecar sao problemas diferentes. Isolar primeiro,')
    print('   como na aula 7, resolve os dois.')
    print()

    # ---------------------------------------------------------------- 5
    print('5. ORDEM DA DEFLACAO E POLIMENTO: QUANTO VALEM, MEDIDO')
    print()
    print('   Os livros recomendam duas defesas contra o acumulo de erro:')
    print('   extrair primeiro as raizes de menor modulo, e refinar cada raiz')
    print('   no polinomio original antes de deflacionar. Vamos medir as duas')
    print('   em 300 polinomios de grau 10 com raizes sorteadas em [-5, 5],')
    print('   em vez de num exemplo escolhido a dedo.')
    print()
    ger = np.random.default_rng(20261122)
    ganha_c = ajuda_p = 0
    razao_o, razao_p = [], []
    for _ in range(300):
        rz = ger.uniform(-5, 5, 10)
        Q = list(np.poly(rz))
        asc = sorted(rz, key=abs)
        chu_a = [v + 0.05 for v in asc]
        chu_d = [v + 0.05 for v in asc[::-1]]

        def pior(ap):
            return max(min(abs(a - v) for v in rz) for a in ap)
        ec = pior(extrair_raizes(Q, chu_a, True)[0])
        ed = pior(extrair_raizes(Q, chu_d, True)[0])
        es = pior(extrair_raizes(Q, chu_a, False)[0])
        if ec < ed:
            ganha_c += 1
        if es > ec:
            ajuda_p += 1
        razao_o.append(ed / max(ec, 1e-300))
        razao_p.append(es / max(ec, 1e-300))
    print('      ordem crescente de modulo vence em %d dos 300 casos' % ganha_c)
    print('         razao decrescente/crescente: mediana %.2f, media'
          % np.median(razao_o))
    print('         geometrica %.2f' % np.exp(np.mean(np.log(razao_o))))
    print('      polir no original ajuda em %d dos 300 casos' % ajuda_p)
    print('         razao sem/com polimento: mediana %.2f, media geometrica %.2f'
          % (np.median(razao_p), np.exp(np.mean(np.log(razao_p)))))
    print()
    print('   Ou seja: as duas regras estao na direcao certa, mas o ganho')
    print('   tipico e de alguns por cento, nao de ordens de grandeza. Onde a')
    print('   diferenca aparece de verdade e num polinomio mal condicionado:')
    print()
    W10 = list(np.poly(np.arange(1, 11)))
    exatas = np.arange(1.0, 11.0)
    for polir in (False, True):
        linha = []
        for nome, ordem in (('crescente', list(exatas)),
                            ('decrescente', list(exatas)[::-1])):
            ap, _ = extrair_raizes(W10, [v + 0.05 for v in ordem], polir)
            linha.append(max(min(abs(a - v) for v in exatas) for a in ap))
        print('      (x-1)...(x-10)  %-14s crescente %.2e   decrescente %.2e'
              % ('com polimento:' if polir else 'sem polimento:', linha[0], linha[1]))
    print()
    print('   Sem polir, a ordem crescente e cerca de dez vezes melhor. Com')
    print('   polimento, a ordem deixa de importar: o refino no polinomio')
    print('   original apaga o que a deflacao estragou. As duas defesas nao')
    print('   se somam, a segunda substitui a primeira.')
    print()

    # ---------------------------------------------------------------- 6
    print('6. RAIZES MULTIPLAS: O DIAGNOSTICO')
    print()
    print('   Em p(x) = (x-2)^m (x-5)(x+3), Newton puro partindo de 2,4.')
    print('   Numa raiz de multiplicidade m o erro cai por um fator constante')
    print('   L = (m-1)/m, e nao quadraticamente.')
    print()
    print('      m    L medido   L previsto   m estimado   passos de Newton')
    for m in (1, 2, 3, 4):
        c = list(np.poly([2.0] * m + [5.0, -3.0]))
        L, mest, x, passos = diagnostico(c, 2.4)
        print('     %2d    %8s   %8.4f   %10d   %10d'
              % (m, ('%.4f' % L) if m > 1 else 'nenhum', (m - 1) / m, mest, passos))
        assert mest == m
    print()
    print('   Para m = 1 a convergencia e rapida demais para haver razao a')
    print('   medir, e e isso que denuncia a raiz simples: menos de quatro')
    print('   passos acima do piso de ruido. Para m de 2 a 4 o L medido bate')
    print('   com (m-1)/m na quarta casa, e m = 1/(1-L) acerta sempre.')
    print()
    print('   O erro final tambem obedece a uma lei. Perto de uma raiz de')
    print('   multiplicidade m, p ~ (x-r)^m, de modo que |p| cai abaixo do')
    print('   ruido do arredondamento a uma distancia da ordem de eps^(1/m):')
    print()
    print('      m    erro medido   eps^(1/m)    razao')
    for m in (2, 3, 4, 5):
        c = list(np.poly([2.0] * m + [5.0, -3.0]))
        x, _ = newton_pol(c, 2.4)
        print('     %2d    %.3e     %.3e    %5.2f'
              % (m, abs(x - 2.0), EPS ** (1.0 / m), abs(x - 2.0) / EPS ** (1.0 / m)))
    print()
    print('   Uma raiz quadrupla em float64 nao pode ser localizada melhor que')
    print('   na quarta casa decimal. Nao e defeito do metodo: a informacao')
    print('   nao esta la. E a razao nao e uma constante: varrendo 40 chutes')
    print('   iniciais entre 2,05 e 3,0 para m = 4,')
    erros = [abs(newton_pol(list(np.poly([2.0] * 4 + [5.0, -3.0])), x0)[0] - 2.0)
             for x0 in np.linspace(2.05, 3.0, 40)]
    print('      erro minimo %.2e, mediana %.2e, maximo %.2e,'
          % (min(erros), float(np.median(erros)), max(erros)))
    print('      com eps^(1/4) = %.2e no meio dessa faixa.' % EPS ** 0.25)
    print('   Isto e, eps^(1/m) e a ESCALA da incerteza, nao um limite que se')
    print('   possa citar com tres digitos.')
    print()
    print('   Newton modificado, x - m p/p\', recupera a convergencia:')
    print()
    print('      m    passos simples   erro      passos modificado   erro')
    for m in (2, 3, 4):
        c = list(np.poly([2.0] * m + [5.0, -3.0]))
        x1, k1 = newton_pol(c, 2.4)
        xm, km = newton_pol(c, 2.4, multiplicidade=m)
        print('     %2d    %10d     %.2e   %13d      %.2e'
              % (m, k1, abs(x1 - 2.0), km, abs(xm - 2.0)))
    print()
    print('   Menos passos E mais precisao, porque a iteracao chega perto')
    print('   antes de o ruido dominar. Varrendo os mesmos 40 chutes:')
    print()
    c4 = list(np.poly([2.0] * 4 + [5.0, -3.0]))
    for mult in (1, 4):
        e = [abs(newton_pol(c4, x0, multiplicidade=mult)[0] - 2.0)
             for x0 in np.linspace(2.05, 3.0, 40)]
        print('      passo x%d: mediana %.2e, pior %.2e, %d chutes perdidos'
              % (mult, float(np.median(e)), max(e), sum(1 for v in e if v > 1e-2)))
    print()
    print('   Nenhum chute perdido, e a mediana trinta vezes melhor. Mas isso')
    print('   depende do resguardo de newton_pol, que guarda o melhor ponto')
    print('   visto: um Newton modificado ingenuo, que aceita o ultimo ponto,')
    print('   diverge em parte desses chutes, porque o passo multiplicado')
    print('   atravessa a raiz quando ainda esta longe.')
    print()

    # ---------------------------------------------------------------- 7
    print('7. CONDICIONAMENTO: O POLINOMIO DE WILKINSON')
    print()
    print('   W(x) = (x-1)(x-2)...(x-10). Perturbamos so o coeficiente de')
    print('   x^9, que vale -55, por um fator (1 + delta), e recalculamos.')
    print()
    print('      delta        maior deslocamento   raizes complexas')
    for delta in (1e-10, 1e-8, 1e-7, 1e-6, 1e-5):
        Wp = np.array(W10, dtype=float)
        Wp[1] *= (1.0 + delta)
        rz = np.roots(Wp)
        desl = max(abs(z - (i + 1)) for i, z in
                   enumerate(sorted(rz, key=lambda z: z.real)))
        nc = sum(1 for z in rz if abs(z.imag) > 1e-8)
        print('      %.0e       %.4e            %d' % (delta, desl, nc))
    print()
    print('   Entre 1e-10 e 1e-7 o deslocamento e proporcional a delta a menos')
    print('   de 1%, como manda a teoria de primeira ordem. A previsao vem do')
    print('   numero de condicao de cada raiz em relacao ao coeficiente a_k:')
    print()
    print('      dx_i / da_k = - x_i^k / p\'(x_i)')
    print()
    print('      raiz   amplificacao |x^9 a_9 / p\'|   deslocamento previsto')
    print('                                           para delta = 1e-7')
    dW = np.polyder(W10)
    for i in (1, 2, 5, 8, 9, 10):
        amp = abs(float(i) ** 9 / np.polyval(dW, float(i))) * abs(W10[1])
        print('      %4d   %22.3e   %18.3e' % (i, amp, amp * 1e-7))
    Wp = np.array(W10, dtype=float)
    Wp[1] *= (1.0 + 1e-7)
    rz = np.roots(Wp)
    med = max(abs(z - (i + 1)) for i, z in enumerate(sorted(rz, key=lambda z: z.real)))
    amp8 = abs(8.0 ** 9 / np.polyval(dW, 8.0)) * abs(W10[1])
    print()
    print('      previsto para a raiz 8:  %.3e' % (amp8 * 1e-7))
    print('      maior deslocamento medido: %.3e' % med)
    assert abs(med - amp8 * 1e-7) / med < 0.05
    print('      concordam em %.1f%%' % (100 * abs(med - amp8 * 1e-7) / med))
    print()
    print('   A teoria tambem preve sua propria falencia. Quando o')
    print('   deslocamento chega a metade da distancia entre duas raizes')
    print('   vizinhas, elas colidem e saem do eixo real como par complexo:')
    print('   e o que se ve na tabela acima em delta = 1e-6, com deslocamento')
    print('   0,73 e quatro raizes complexas.')
    print()
    print('   E o grau 20, do experimento original de Wilkinson? Em float64')
    print('   ele nao e sequer montavel:')
    print()
    for n in (10, 20):
        exato = [1]
        for i in range(1, n + 1):
            novo = [0] * (len(exato) + 1)
            for j, a in enumerate(exato):
                novo[j] += a
                novo[j + 1] += -i * a
            exato = novo
        Wn = np.poly(np.arange(1, n + 1))
        rep = max(abs(float(e) - w) / max(abs(e), 1) for e, w in zip(exato, Wn))
        desvios = [(abs(z - (i + 1)), i + 1) for i, z in
                   enumerate(sorted(np.roots(Wn), key=lambda z: z.real))]
        err, qual = max(desvios)
        print('      grau %2d: maior coeficiente %.4e  (2^53 = %.2e)'
              % (n, max(abs(a) for a in exato), 2.0 ** 53))
        print('               erro ao guardar os coeficientes %.2e' % rep)
        print('               erro das raizes do polinomio NAO perturbado %.4f'
              % err)
        print('               (a pior e a raiz %d)' % qual)
    print()
    print('   No grau 20 o maior coeficiente passa de 2^53, de modo que')
    print('   escrever o polinomio ja o perturba, e np.roots erra uma das')
    print('   raizes em 0,07 sem que ninguem tenha perturbado nada. O')
    print('   experimento classico, em precisao dupla, mede duas vezes o mesmo')
    print('   fenomeno. No grau 10 os coeficientes cabem exatos, os erros')
    print('   sao zero, e a medida e limpa. Por isso a aula usa o grau 10.')
    print()

    # ---------------------------------------------------------------- 8
    print('8. BAIRSTOW: PARES COMPLEXOS COM ARITMETICA REAL')
    print()
    print('   Em vez de procurar uma raiz, procura-se um fator x^2 - ux - v,')
    print('   ajustando u e v por Newton em duas variaveis. Se o par for')
    print('   complexo, ele aparece nas raizes do fator, e nenhum numero')
    print('   complexo e usado no caminho.')
    print()
    pb = [1.0, 1.0, -5.0, 1.0, -6.0]          # (x^2+1)(x-2)(x+3)
    print('   p(x) = (x^2 + 1)(x - 2)(x + 3) = x^4 + x^3 - 5x^2 + x - 6')
    print()
    print('      palpite (u,v)    iteracoes   fator encontrado        raizes')
    for u0, v0 in ((0.5, 0.5), (-1.0, -2.0), (0.0, 0.0), (2.0, -1.0)):
        res = bairstow(pb, u0, v0)
        if res is None:
            print('      (%5.1f,%5.1f)       nao convergiu' % (u0, v0))
            continue
        u, v, q, it = res
        rz = np.roots([1.0, -u, -v])
        tipo = 'complexas' if abs(rz[0].imag) > 1e-9 else 'reais'
        print('      (%5.1f,%5.1f)   %9d   x^2 %+.4fx %+.4f   %s %s'
              % (u0, v0, it, -u + 0.0, -v + 0.0,
                 ' '.join('%+.3f' % (z.real + 0.0) if abs(z.imag) < 1e-9
                          else '%+.2f%+.2fi' % (z.real + 0.0, z.imag) for z in rz),
                 tipo))
    u, v, q, it = bairstow(pb, 0.5, 0.5)
    print()
    print('   Partindo de (0,5; 0,5) sao %d iteracoes, e o fator e' % it)
    print('   x^2 + x - 6 = (x-2)(x+3), as duas raizes REAIS. O par complexo')
    print('   fica no quociente, %s, cujas raizes sao +-i.'
          % ' '.join('%g' % a for a in q))
    print('   Bairstow acha UM fator quadratico, o da bacia onde caiu o')
    print('   palpite, e nao ha como escolher qual de antemao.')
    print()

    # ---------------------------------------------------------------- 9
    print('9. APLICACAO: MODOS NORMAIS DE TRES MASSAS')
    print()
    print('   Tres massas iguais m, ligadas por quatro molas iguais k entre')
    print('   paredes fixas. Com x_i = A_i exp(i omega t), a equacao')
    print('   m x_i\'\' = k(x_{i-1} - 2x_i + x_{i+1}) da o problema de')
    print('   autovalores cuja equacao secular e')
    print()
    print('      lambda^3 - 6 lambda^2 + 10 lambda - 4 = 0,   lambda = m w^2/k')
    print()
    secular = [1.0, -6.0, 10.0, -4.0]
    print('   Descartes ja garante a fisica: a sequencia (+,-,+,-) tem tres')
    print('   variacoes, e p(-x) nao tem nenhuma. Logo as tres raizes sao')
    print('   positivas, e nao ha modo com frequencia imaginaria, que seria')
    print('   instabilidade num sistema conservativo.')
    print()
    lam, restos = extrair_raizes(secular, [0.5, 2.0, 5.0], polir=True)
    lam = sorted(lam)
    K = np.array([[2.0, -1.0, 0.0], [-1.0, 2.0, -1.0], [0.0, -1.0, 2.0]])
    mat = sorted(np.linalg.eigvalsh(K))
    fechado = sorted(4 * np.sin(j * np.pi / 8) ** 2 for j in (1, 2, 3))
    print('      modo   nossa deflacao      eigvalsh         4 sen^2(j pi/8)')
    for j in range(3):
        print('      %4d   %.14f   %.14f   %.14f'
              % (j + 1, lam[j], mat[j], fechado[j]))
    assert max(abs(a - b) for a, b in zip(lam, fechado)) < 1e-12
    print()
    print('      w/w0 = %s' % '  '.join('%.6f' % np.sqrt(v) for v in lam))
    print('      maior discordancia entre os tres caminhos: %.2e'
          % max(abs(a - b) for a, b in zip(lam, fechado)))
    print()
    print('   Os tres caminhos coincidem em doze casas. Mas eles nao')
    print('   envelhecem igual. Para N massas o polinomio caracteristico tem')
    print('   grau N, e seus coeficientes crescem como os de Wilkinson:')
    print()
    print('      N    maior coeficiente   via np.poly + np.roots   via eigvalsh')
    for N in (3, 5, 8, 12, 16, 24):
        KN = (np.diag([2.0] * N) + np.diag([-1.0] * (N - 1), 1)
              + np.diag([-1.0] * (N - 1), -1))
        car = np.poly(KN)
        lamN = np.sort(np.roots(car).real)
        exa = np.sort([4 * np.sin(j * np.pi / (2 * (N + 1))) ** 2
                       for j in range(1, N + 1)])
        print('      %2d   %17.4e   %18.2e   %14.2e'
              % (N, np.max(np.abs(car)), np.max(np.abs(lamN - exa)),
                 np.max(np.abs(np.sort(np.linalg.eigvalsh(KN)) - exa))))
    print()
    print('   A rota polinomial perde cerca de tres casas a cada quatro')
    print('   massas e chega a')
    print('   N = 24 sem nenhum digito confiavel. A rota matricial, que nunca')
    print('   expande o polinomio caracteristico, continua no nivel do')
    print('   arredondamento. Saber quando NAO usar polinomios e o fim desta')
    print('   aula.')
    print()
    print('=' * 68)
    print('  Todas as conferencias passaram.')
    print('=' * 68)
    print()


if __name__ == '__main__':
    main()
