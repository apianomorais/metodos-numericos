# -*- coding: utf-8 -*-
"""Ponto fixo: uma desigualdade que explica todos os métodos iterativos.

O QUE RESOLVE
    1. Roda as quatro funções de iteração da mesma equação e mostra que
       o destino de cada uma está escrito em |phi'| na raiz.
    2. Mostra que a escolha de phi decide QUAL raiz se alcança, e não
       apenas com que velocidade.
    3. Mede a estimativa de erro L/(1-L) e exibe o quanto a diferença
       entre iterados subestima o erro quando L se aproxima de 1.
    4. Acelera com Aitken e Steffensen, e verifica que a ordem sobe de
       1 para 2 sem usar derivada nenhuma.
    5. Resolve o equilíbrio radiativo de um planeta, calibrando o
       coeficiente de efeito estufa contra a temperatura observada.

A IDEIA
    Toda equacao f(x) = 0 pode ser reescrita como x = phi(x), e de
    infinitas maneiras. Iterando x_{k+1} = phi(x_k) a partir de um chute,
    a sequencia converge para a raiz, diverge, oscila ou vagueia, e o que
    decide entre os quatro destinos e uma unica quantidade: |phi'| perto
    da raiz.

    Pelo teorema do valor medio, e_{k+1} = phi'(c) e_k para algum c entre
    x_k e a raiz. Se |phi'| <= L < 1 numa vizinhanca, o erro e
    multiplicado por L a cada passo e vai a zero geometricamente. Se
    |phi'| > 1, ele cresce. E se phi'(raiz) = 0, o termo linear some e
    sobra o quadratico: convergencia quadratica.

    Essa desigualdade nao e um detalhe desta aula. Ela e o esqueleto de
    quase todo metodo iterativo do calculo numerico, e reaparece como
    raio espectral na convergencia de Jacobi e Gauss-Seidel, e como
    condicao de estabilidade em integracao de equacoes diferenciais.

COMO CONFERIR SE ESTA CERTO
    1. A classificacao prevista por |phi'(raiz)| tem de bater com o que
       cada iteracao faz de fato, e o programa roda as quatro.
    2. A taxa medida de convergencia linear tem de dar |phi'(raiz)|, e
       da em cinco casas.
    3. A razao entre o erro real e |x_k - x_(k-1)| tem de dar L/(1-L), e
       o programa usa uma phi linear, em que L e exato, para testar.
    4. A ordem de Steffensen tem de ser 2, conferida pela razao
       e_(k+1)/e_k^2, que fica constante.
    5. A temperatura de equilibrio tem de reproduzir a observada quando
       o coeficiente e calibrado por ela, e o programa calibra.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import math

import numpy as np
from scipy.constants import sigma


# ---------------------------------------------------------------------------


def ponto_fixo(phi, x0, tol=1e-12, nmax=500, historico=None):
    """Iteração de ponto fixo. Devolve (raiz, iteracoes, motivo)."""
    x = float(x0)
    for k in range(1, nmax + 1):
        try:
            xn = phi(x)
        except (OverflowError, ValueError, ZeroDivisionError):
            return x, k, 'estourou'
        if not np.isfinite(xn) or abs(xn) > 1e100:
            return xn, k, 'divergiu'
        if historico is not None:
            historico.append(xn)
        if abs(xn - x) < tol:
            return xn, k, 'convergiu'
        x = xn
    return x, nmax, 'teto de iteracoes'


def steffensen(phi, x0, tol=1e-12, nmax=100, historico=None):
    """Aitken aplicado dentro do laço: ordem 2 sem derivada nenhuma."""
    x = float(x0)
    for k in range(1, nmax + 1):
        x1 = phi(x)
        x2 = phi(x1)
        den = x2 - 2 * x1 + x
        if abs(den) < 1e-18:
            return x1, k, 'denominador nulo'
        xn = x - (x1 - x) ** 2 / den
        if historico is not None:
            historico.append(xn)
        if abs(xn - x) < tol:
            return xn, k, 'convergiu'
        x = xn
    return x, nmax, 'teto de iteracoes'


# ---------------------------------------------------------------------------


def main():
    print('=' * 72)
    print('1. QUATRO PHI PARA A MESMA EQUACAO')
    print('=' * 72)
    print('   f(x) = x^2 - x - 2 = 0, com raizes 2 e -1. Isolando x de')
    print('   quatro maneiras diferentes, todas com phi(2) = 2:')
    print()
    FIS = [
        ('phi1 = x^2 - 2', lambda x: x * x - 2, lambda x: 2 * x),
        ('phi2 = raiz(x+2)', lambda x: math.sqrt(x + 2),
         lambda x: 0.5 / math.sqrt(x + 2)),
        ('phi3 = 1 + 2/x', lambda x: 1 + 2 / x, lambda x: -2 / (x * x)),
        ('phi4 = (x^2+2)/(2x-1)', lambda x: (x * x + 2) / (2 * x - 1),
         lambda x: (2 * x * (2 * x - 1) - 2 * (x * x + 2)) / (2 * x - 1) ** 2),
    ]
    print('     k  ' + '  '.join('%16s' % n[:16] for n, _, _ in FIS))
    xs = [2.5] * 4
    for k in range(6):
        linha = '    %2d  ' % k
        for i, (n, p, d) in enumerate(FIS):
            v = xs[i]
            linha += '  %16s' % ('%.8f' % v if abs(v) < 1e6 else '%.3e' % v)
            try:
                xs[i] = p(v)
            except (OverflowError, ValueError, ZeroDivisionError):
                xs[i] = float('inf')
        print(linha)
    print()
    print('   O mesmo problema, o mesmo ponto de partida, quatro destinos.')
    print('   E a quantidade que decide e uma so:')
    print()
    print('      funcao de iteracao       |phi\'(2)|   previsao')
    for n, p, d in FIS:
        L = abs(d(2.0))
        if L > 1:
            prev = 'diverge'
        elif L == 0:
            prev = 'quadratica'
        else:
            prev = 'linear, taxa %.2f' % L
        print('      %-24s  %7.4f   %s' % (n, L, prev))
    print()
    print('   Conferindo a taxa medida contra |phi\'(2)|:')
    print()
    print('      funcao            taxa prevista   taxa medida   iteracoes')
    for n, p, d in FIS:
        L = abs(d(2.0))
        if L >= 1:
            print('      %-18s  %11s   %11s   %s' % (n[:18], 'diverge', '—', '—'))
            continue
        if L == 0:
            r, k, mot = ponto_fixo(p, 2.5, tol=1e-13)
            print('      %-18s  %11s   %11s   %9d'
                  % (n[:18], 'quadratica', 'nao linear', k))
            continue
        h = []
        r, k, mot = ponto_fixo(p, 2.5, tol=1e-13, historico=h)
        # a razao so vale longe do piso de arredondamento: perto dele o
        # erro ja e ruido e a taxa medida cai para 0,248 em vez de 0,250
        e = [abs(v - 2.0) for v in h if abs(v - 2.0) > 1e-11]
        taxa = e[-1] / e[-2] if len(e) > 2 else float('nan')
        print('      %-18s  %11.5f   %11.5f   %9d'
              % (n[:18], L, taxa, k))
    print()
    print('   phi4 nao e uma escolha qualquer: ela E o metodo de Newton')
    print('   para esta equacao, porque x - f/f\' = (x^2+2)/(2x-1). E o')
    print('   phi\'(2) = 0 de Newton e a convergencia quadratica da aula 5,')
    print('   vista do angulo do ponto fixo.')
    print()

    print('=' * 72)
    print('2. A ESCOLHA DE PHI DECIDE QUAL RAIZ')
    print('=' * 72)
    print('   A equacao tem DUAS raizes, 2 e -1. Partindo de x0 = -1,3,')
    print('   que esta pertinho de -1:')
    print()
    print('      funcao de iteracao       |phi\'(-1)|   destino')
    for n, p, d in FIS:
        try:
            fixo = abs(p(-1.0) + 1.0) < 1e-12
            Ls = '%8.4f' % abs(d(-1.0)) if fixo else '  nem é '
        except (ValueError, ZeroDivisionError):
            Ls = '     —  '
        r, k, mot = ponto_fixo(p, -1.3, tol=1e-13, nmax=300)
        if mot == 'convergiu':
            dest = 'raiz %+.6f em %d passos' % (r, k)
        else:
            dest = mot
        print('      %-24s %s   %s' % (n, Ls, dest))
    print()
    print('   So phi4 alcanca a raiz -1, e o motivo esta na coluna do meio:')
    print('   ela e a unica com |phi\'(-1)| < 1. As outras sao REPELIDAS')
    print('   daquela raiz, por mais perto que se comece.')
    print()
    print('   Repare que phi2 nem tem -1 como ponto fixo: raiz(-1+2) = 1,')
    print('   e nao -1. A raiz quadrada so devolve o ramo positivo, de modo')
    print('   que a reescrita perdeu uma das raizes pelo caminho.')
    print()
    print('   E phi1 merece um paragrafo. A partir de -1,3 ela nao diverge')
    print('   nem converge:')
    p1 = lambda x: x * x - 2
    x, vals = -1.3, []
    for _ in range(300):
        x = p1(x)
        vals.append(x)
    print('      primeiros valores: %s'
          % ' '.join('%+.4f' % v for v in vals[:8]))
    print('      ultimos valores:   %s'
          % ' '.join('%+.4f' % v for v in vals[-8:]))
    print('      extremos dos ultimos 200: %+.3f a %+.3f'
          % (min(vals[100:]), max(vals[100:])))
    a, b = -1.3, -1.3 + 1e-12
    for _ in range(60):
        a, b = p1(a), p1(b)
    print('      duas condicoes iniciais a 1e-12 de distancia, 60 passos')
    print('      depois: %+.6f e %+.6f, separadas por %.3f' % (a, b, abs(a - b)))
    print()
    print('   A orbita fica presa em [-2, 2] e nunca se decide: o mapa')
    print('   x -> x^2 - 2 e conjugado a 2cos(2t) e e CAOTICO. Nenhum dos')
    print('   quatro destinos do livro-texto (converge, diverge, oscila')
    print('   convergindo) descreve isso, e e o que mais acontece quando')
    print('   |phi\'| > 1 num intervalo limitado.')
    print()

    print('=' * 72)
    print('3. A ESTIMATIVA DE ERRO, E QUANDO ELA ENGANA')
    print('=' * 72)
    print('   A unica coisa que se mede durante o laco e |x_k - x_(k-1)|.')
    print('   O teorema promete')
    print()
    print('      |x_k - raiz| <= L/(1-L) |x_k - x_(k-1)|')
    print()
    print('   Testando com phi(x) = raiz + L(x - raiz), em que L e exato:')
    print()
    print('        L      erro real    |x_k - x_(k-1)|    razao   L/(1-L)')
    for L in (0.25, 0.5, 0.9, 0.99):
        ksi = 2.0
        p = lambda x, L=L: ksi + L * (x - ksi)
        x = 2.5
        for _ in range(10):
            xa, x = x, p(x)
        erro, dif = abs(x - ksi), abs(x - xa)
        print('      %5.2f    %.3e      %.3e      %6.2f    %6.2f'
              % (L, erro, dif, erro / dif, L / (1 - L)))
    print()
    print('   A razao medida reproduz L/(1-L) em todas as casas. E o recado')
    print('   esta na ultima linha: com L = 0,99 a diferenca entre iterados')
    print('   SUBESTIMA o erro real por um fator 99.')
    print()
    print('   Dai o aviso: convergencia lenta e traicoeira, porque PARECE')
    print('   convergencia. Os iterados mal se mexem, o criterio de parada')
    print('   se declara satisfeito, e a resposta esta a cem diferenças de')
    print('   distancia da raiz. Antes de confiar em |x_k - x_(k-1)|, estime')
    print('   L.')
    print()

    print('=' * 72)
    print('4. AITKEN E STEFFENSEN: ORDEM 2 SEM DERIVADA')
    print('=' * 72)
    print('   Se o erro cai como e_(k+1) = C e_k, tres iterados consecutivos')
    print('   bastam para extrapolar onde a sequencia vai dar:')
    print()
    print('      x_chapeu = x_k - (x_(k+1) - x_k)^2 / (x_(k+2) - 2x_(k+1) + x_k)')
    print()
    p2 = lambda x: math.sqrt(x + 2)
    h1 = []
    r1, n1, _ = ponto_fixo(p2, 2.5, tol=1e-12, historico=h1)
    h2 = []
    r2, n2, _ = steffensen(p2, 2.5, tol=1e-12, historico=h2)
    print('   Em phi2 = raiz(x+2), a partir de 2,5:')
    print('      ponto fixo simples: %.14f em %2d iteracoes' % (r1, n1))
    print('      Steffensen        : %.14f em %2d iteracoes' % (r2, n2))
    print('      (cada passo de Steffensen gasta 2 avaliacoes de phi, de')
    print('       modo que a comparacao justa e %d contra %d avaliacoes)'
          % (n1, 2 * n2))
    print()
    print('   A ordem, conferida pela razao e_(k+1)/e_k^2, que fica')
    print('   constante quando a convergencia e quadratica:')
    print()
    e = [abs(v - 2.0) for v in h2 if abs(v - 2.0) > 0]
    print('      em float64: %s' % ' '.join('%.3e' % v for v in e))
    print('      e a razao: %s'
          % ' '.join('%.4f' % (e[i + 1] / e[i] ** 2) for i in range(len(e) - 1)))
    print()
    print('   Essa medida nao serve, e por um motivo que ja apareceu na')
    print('   aula 3: Steffensen chega ao piso de arredondamento em TRES')
    print('   passos, e a ultima razao sai de um erro que ja e ruido. Para')
    print('   medir ordem e preciso precisao de sobra, e o mpmath da:')
    print()
    try:
        from mpmath import mp, mpf, sqrt as msqrt
        mp.dps = 80
        pm = lambda x: msqrt(x + 2)
        xm, em = mpf('2.5'), []
        for _ in range(6):
            a1 = pm(xm)
            a2 = pm(a1)
            den = a2 - 2 * a1 + xm
            if abs(den) < mpf('1e-70'):
                break
            xm = xm - (a1 - xm) ** 2 / den
            em.append(abs(xm - 2))
            if em[-1] < mpf('1e-60'):
                break
        print('      em 80 digitos: %s'
              % ' '.join(mp.nstr(v, 4) for v in em))
        print('      razao e_(k+1)/e_k^2: %s'
              % ' '.join(mp.nstr(em[i + 1] / em[i] ** 2, 5)
                         for i in range(len(em) - 2)))
        print('      ordem estimada: %s'
              % ' '.join('%.4f' % float(mp.log(em[i + 2] / em[i + 1])
                                        / mp.log(em[i + 1] / em[i]))
                         for i in range(len(em) - 3)))
        print()
        print('   A razao fica em 0,00521 e a ordem da 2,0000 nos dois')
        print('   intervalos utilizaveis: Steffensen e mesmo quadratico, e')
        print('   sem ter visto uma derivada.')
    except ImportError:
        print('      (instale mpmath para esta medida: pip install mpmath)')
    e1 = [abs(v - 2.0) for v in h1 if abs(v - 2.0) > 1e-14]
    print('      erros do ponto fixo simples, razao e_(k+1)/e_k:')
    print('         %s' % ' '.join('%.4f' % (e1[i + 1] / e1[i])
                                   for i in range(len(e1) - 4, len(e1) - 1)))
    print('      que e o |phi\'(2)| = 0,25 previsto: ordem 1.')
    print()
    print('   Steffensen e a resposta certa para uma situacao comum: existe')
    print('   uma iteracao natural para o problema, vinda da propria fisica,')
    print('   que converge devagar, e nao ha derivada a mao.')
    print()

    print('=' * 72)
    print('5. A TEMPERATURA DE EQUILIBRIO DE UM PLANETA')
    print('=' * 72)
    print('   Um planeta em equilibrio radiativo emite tanto quanto absorve.')
    print('   Com um termo simplificado de efeito estufa, proporcional a T:')
    print()
    print('      sigma T^4 = S(1-a)/4 + beta T')
    print()
    print('   Isolando T da potencia quarta sai a forma de ponto fixo:')
    print()
    print('      T = phi(T) = [ (S(1-a)/4 + beta T) / sigma ]^(1/4)')
    print()
    S, alb = 1361.0, 0.30
    absorvido = S * (1 - alb) / 4
    print('   Com S = %.0f W/m2 e albedo %.2f, o fluxo absorvido e %.2f W/m2.'
          % (S, alb, absorvido))
    print()
    print('   Sem atmosfera (beta = 0), a conta e direta:')
    Tef = (absorvido / sigma) ** 0.25
    print('      T_efetiva = %.2f K = %.2f C' % (Tef, Tef - 273.15))
    print('   A Terra observada tem media global de 288 K, ou 15 C. A')
    print('   diferenca de 33 K e o efeito estufa, e e ela que o beta')
    print('   representa.')
    print()
    print('   O VALOR de beta nao se tira do nada: ele se calibra pela')
    print('   temperatura observada.')
    Tobs = 288.0
    beta = (sigma * Tobs ** 4 - absorvido) / Tobs
    print('      emissao a 288 K = sigma T^4 = %.2f W/m2' % (sigma * Tobs ** 4))
    print('      beta = (%.2f - %.2f)/288 = %.4f W/m2/K'
          % (sigma * Tobs ** 4, absorvido, beta))
    print()
    print('   Rodando a iteracao com esse beta, de varios chutes:')
    print()
    phiT = lambda T: ((absorvido + beta * T) / sigma) ** 0.25
    dphiT = lambda T: 0.25 * ((absorvido + beta * T) / sigma) ** (-0.75) * beta / sigma
    print('        T0 (K)     T de equilibrio      iteracoes')
    for T0 in (1.0, 100.0, 288.0, 1000.0, 5000.0):
        T, k, mot = ponto_fixo(phiT, T0, tol=1e-10)
        print('      %8.1f     %10.3f K        %4d' % (T0, T, k))
    T, k, _ = ponto_fixo(phiT, 200.0, tol=1e-10)
    print()
    print('   Todos caem no mesmo lugar, e o motivo e |phi\'| = %.4f na'
          % abs(dphiT(T)))
    print('   raiz: a potencia um quarto achata qualquer variacao de T, de')
    print('   modo que a iteracao e fortemente contrativa e a bacia de')
    print('   atracao e praticamente toda a reta positiva. Nao e preciso')
    print('   chutar bem.')
    print()
    print('   Com o modelo calibrado, da para perguntar o que muda quando')
    print('   o albedo muda:')
    print()
    print('        albedo    T de equilibrio     desvio')
    for a2 in (0.25, 0.28, 0.30, 0.32, 0.35):
        fl = S * (1 - a2) / 4
        ph = lambda T, fl=fl: ((fl + beta * T) / sigma) ** 0.25
        T2, _, _ = ponto_fixo(ph, 200.0, tol=1e-10)
        print('        %.2f      %8.2f K        %+6.2f K' % (a2, T2, T2 - Tobs))
    print()
    print('   Cinco centesimos de albedo valem uns 3,5 K, o que da ideia da')
    print('   sensibilidade do clima a cobertura de nuvens e de gelo. Convem')
    print('   lembrar que o modelo e grosseiro: um termo linear em T e uma')
    print('   caricatura do efeito estufa, calibrada por um unico ponto.')
    print('   Ele serve para ver a iteracao funcionando, e nao para prever')
    print('   clima.')
    print()


if __name__ == '__main__':
    main()
