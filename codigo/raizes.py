# -*- coding: utf-8 -*-
"""Raízes de equações: bisseção, Newton-Raphson e secante.

O QUE RESOLVE
    1. Compara os três métodos no mesmo problema, contando iterações.
    2. MEDE a ordem de convergência de cada um, em vez de afirmá-la, e
       confere contra 1, 2 e a razão áurea.
    3. Exibe as três maneiras de Newton falhar, cada uma com um exemplo
       que falha de verdade quando o programa roda.
    4. Mostra por que o critério de parada ingênuo engana, e qual usar.
    5. Resolve a equação de van der Waals para o volume molar, que é o
       caso em que um físico encontra isto pela primeira vez.

A IDEIA
    Bisseção nao usa nenhuma informacao sobre a funcao alem do sinal, e
    por isso e lenta e nunca falha: se ha troca de sinal num intervalo,
    ha raiz dentro dele, e cortar o intervalo ao meio garante um digito
    binario por iteracao. E convergencia LINEAR, de razao 1/2.

    Newton usa a derivada, isto e, usa a funcao localmente como se fosse
    uma reta. Quando o chute esta perto da raiz, essa aproximacao e
    excelente e o numero de digitos corretos DOBRA a cada passo: e
    convergencia quadratica. Quando o chute esta longe, a reta tangente
    pode apontar para qualquer lugar, e nao ha garantia nenhuma.

    A secante troca a derivada analitica por uma diferenca de dois
    pontos. Perde um pouco de velocidade, de ordem 2 para ordem 1,618,
    e ganha nao precisar da derivada, o que importa quando a funcao vem
    de uma tabela ou de outro programa.

COMO CONFERIR SE ESTA CERTO
    1. Todos os metodos tem de convergir para a mesma raiz, e ela tem de
       anular a funcao em precisao de maquina.
    2. A ordem medida pela razao de logaritmos de erros sucessivos tem
       de dar 1 para bisseccao, 2 para Newton e 1,618 para a secante.
    3. Cada exemplo de falha tem de falhar de fato, e o programa diz
       como falhou.
    4. A van der Waals tem de reproduzir o gas ideal no limite de baixa
       pressao, e o volume critico no ponto critico.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import numpy as np
from scipy.optimize import brentq


# ---------------------------------------------------------------------------
# os três métodos, escritos para guardar o histórico
# ---------------------------------------------------------------------------


def bissecao(f, a, b, tol=1e-15, maxit=200):
    """Corta o intervalo ao meio, ficando com o lado que troca de sinal."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError('sem troca de sinal em [%g, %g]' % (a, b))
    hist = []
    for _ in range(maxit):
        m = 0.5 * (a + b)
        hist.append(m)
        if (b - a) / 2 < tol:
            break
        fm = f(m)
        if fa * fm <= 0:
            b, fb = m, fm
        else:
            a, fa = m, fm
    return hist


def newton(f, fl, x0, tol=1e-15, maxit=100):
    """x_{n+1} = x_n - f/f'. Guarda o histórico e o motivo de parar."""
    x = float(x0)
    hist = [x]
    for _ in range(maxit):
        d = fl(x)
        if d == 0.0:
            return hist, 'derivada nula'
        novo = x - f(x) / d
        if not np.isfinite(novo) or abs(novo) > 1e150:
            hist.append(novo)
            return hist, 'divergiu'
        hist.append(novo)
        if abs(novo - x) <= tol * max(1.0, abs(novo)):
            return hist, 'convergiu'
        x = novo
    return hist, 'estourou o limite de iteracoes'


def secante(f, x0, x1, tol=1e-15, maxit=100):
    """A derivada de Newton trocada pela inclinação de dois pontos."""
    f0, f1 = f(x0), f(x1)
    hist = [x0, x1]
    for _ in range(maxit):
        if f1 == f0:
            return hist, 'secante horizontal'
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        hist.append(x2)
        if abs(x2 - x1) <= tol * max(1.0, abs(x2)):
            return hist, 'convergiu'
        x0, f0, x1, f1 = x1, f1, x2, f(x2)
    return hist, 'estourou o limite de iteracoes'


def janela_util(hist, raiz):
    """Os erros que ainda dizem alguma coisa.

    Perto do fim, o erro bate no piso da precisão de máquina e para de
    cair; dali em diante qualquer razão entre erros mede arredondamento
    e não convergência. A janela útil vai do começo até o primeiro erro
    que desce abaixo de cem vezes o épsilon local.
    """
    piso = 100 * np.finfo(float).eps * max(1.0, abs(raiz))
    e = []
    for x in hist:
        v = abs(x - raiz)
        if v <= piso:
            break
        e.append(v)
    return e


def ordem_medida(hist, raiz):
    """A ordem p de |e_{n+1}| ~ C |e_n|^p, por mínimos quadrados.

    Tomar a razão entre dois logaritmos consecutivos, que é o que se vê
    nos livros, funciona para Newton e falha para a bisseção: ali o erro
    não cai por um fator fixo, porque o ponto médio às vezes cai perto
    da raiz por sorte, e a razão de logaritmos fica errática. Ajustar
    uma reta a log|e_{n+1}| contra log|e_n| usa todos os pontos de uma
    vez e faz a média desse ruído.
    """
    e = janela_util(hist, raiz)
    if len(e) < 4:
        return float('nan'), []
    x = np.log(np.array(e[:-1]))
    y = np.log(np.array(e[1:]))
    p = np.polyfit(x, y, 1)[0]
    razoes = [np.log(e[i] / e[i - 1]) / np.log(e[i - 1] / e[i - 2])
              for i in range(2, len(e))
              if abs(np.log(e[i - 1] / e[i - 2])) > 1e-12]
    return p, razoes


def taxa_media(hist, raiz):
    """Para um método linear, o que interessa não é a ordem, que vale 1,
    e sim a razão por que o erro encolhe a cada passo. Ela sai da
    inclinação de log|e_n| contra n."""
    e = janela_util(hist, raiz)
    if len(e) < 4:
        return float('nan')
    coef = np.polyfit(np.arange(len(e)), np.log(np.array(e)), 1)[0]
    return np.exp(coef)


# ---------------------------------------------------------------------------
# van der Waals
# ---------------------------------------------------------------------------

R_GAS = 8.314462618        # J/(mol K)


def vdw_residuo(V, p, T, a, b):
    """(p + a/V^2)(V - b) - RT, que é zero no volume molar correto."""
    return (p + a / V ** 2) * (V - b) - R_GAS * T


def vdw_derivada(V, p, T, a, b):
    """d/dV do resíduo, para Newton. Feita à mão, e conferida numericamente
    na seção 5 contra uma diferença central."""
    return p + a / V ** 2 - 2 * a * (V - b) / V ** 3


def main():
    print('=' * 72)
    print('1. OS TRES METODOS NO MESMO PROBLEMA')
    print('=' * 72)
    print('   A equacao x^3 - 2x - 5 = 0, que Newton usou no artigo de')
    print('   1669 e que virou o exemplo canonico. A raiz real fica entre')
    print('   2 e 3.')
    print()
    f = lambda x: x ** 3 - 2 * x - 5
    fl = lambda x: 3 * x ** 2 - 2
    raiz = brentq(f, 2, 3, xtol=1e-16, rtol=8.9e-16)
    print('   raiz de referencia (brentq do SciPy): %.17f' % raiz)
    print('   residuo nessa raiz: %.3e' % f(raiz))
    print()

    hb = bissecao(f, 2.0, 3.0)
    hn, mn_ = newton(f, fl, 3.0)
    hs, ms_ = secante(f, 2.0, 3.0)
    print('      metodo        iteracoes   |x - raiz| final   residuo')
    for nome, h in (('bisseccao', hb), ('Newton', hn), ('secante', hs)):
        print('      %-12s  %9d   %16.3e   %9.2e'
              % (nome, len(h) - 1, abs(h[-1] - raiz), f(h[-1])))
    print()
    print('   Bisseccao precisa de %d iteracoes para o que Newton faz em'
          % (len(hb) - 1))
    print('   %d. A diferenca nao e de implementacao: e a diferenca entre'
          % (len(hn) - 1))
    print('   ganhar um digito binario por passo e dobrar o numero de')
    print('   digitos corretos por passo.')
    print()
    print('   Os primeiros passos de cada um, para ver a diferenca:')
    print()
    print('      n     bisseccao          Newton             secante')
    for i in range(8):
        linha = '      %d  ' % i
        for h in (hb, hn, hs):
            linha += '  %18.15f' % h[i] if i < len(h) else '  %18s' % ''
        print(linha)
    print()

    print('=' * 72)
    print('2. A ORDEM DE CONVERGENCIA, MEDIDA')
    print('=' * 72)
    print('   Se |e_{n+1}| ~ C |e_n|^p, tomar o logaritmo da relacao da')
    print('   uma reta de inclinacao p. Ajustando essa reta aos proprios')
    print('   historicos acima, e descartando os ultimos pontos, em que o')
    print('   erro ja bateu no piso da precisao de maquina:')
    print()
    print('      metodo       pontos uteis   ordem medida   prevista   erro')
    for nome, h, prev in (('bisseccao', hb, 1.0),
                          ('Newton', hn, 2.0),
                          ('secante', hs, (1 + 5 ** 0.5) / 2)):
        pm, _ = ordem_medida(h, raiz)
        print('      %-11s %10d   %12.4f   %8.4f  %5.1f%%'
              % (nome, len(janela_util(h, raiz)), pm, prev,
                 100 * abs(pm / prev - 1)))
    print()
    print('   A bisseccao da ordem 1, a secante perto de 1,618 e Newton')
    print('   perto de 2. A razao aurea da secante nao e coincidencia: a')
    print('   recorrencia dos expoentes de erro e p_{n+1} = p_n + 1, cuja')
    print('   razao limite e (1+raiz(5))/2.')
    print()
    print('   Para a bisseccao, porem, a ordem nao e o numero util: toda')
    print('   convergencia linear tem ordem 1, e o que distingue uma da')
    print('   outra e a TAXA, isto e, por quanto o erro encolhe a cada')
    print('   passo.')
    print()
    print('      taxa media medida na bisseccao: %.6f' % taxa_media(hb, raiz))
    print('      prevista: 0,500000, porque o intervalo cai pela metade')
    print()
    print('   Convem dizer por que a medida foi feita por minimos')
    print('   quadrados e nao pela razao entre dois logaritmos')
    print('   consecutivos, que e a forma que aparece nos livros. A razao')
    print('   consecutiva funciona para Newton e falha para a bisseccao,')
    print('   porque ali o erro nao cai por um fator fixo: o ponto medio')
    print('   as vezes cai perto da raiz por sorte e o erro despenca, e no')
    print('   passo seguinte ele volta a subir em relacao ao que seria.')
    print('   Essas estimativas individuais saem assim:')
    print()
    _, rz = ordem_medida(hb, raiz)
    print('      %s' % '  '.join('%.2f' % o for o in rz[:8]))
    print()
    print('   Nenhuma delas vale sozinha, e a media de todas vale.')
    print()

    print('=' * 72)
    print('3. AS TRES MANEIRAS DE NEWTON FALHAR')
    print('=' * 72)
    print()
    print('   (a) Derivada nula, ou quase. A tangente horizontal nao')
    print('       cruza o eixo, e a formula divide por zero.')
    print()
    q = lambda x: x * x - 1.0
    ql = lambda x: 2.0 * x
    h, motivo = newton(q, ql, 0.0)
    print('       x^2 - 1 a partir de x0 = 0, onde f\'(0) = 0 exatamente:')
    print('         %s, na iteracao %d' % (motivo, len(h) - 1))
    print()
    print('       O caso perigoso, porem, nao e esse: a divisao por zero')
    print('       para o programa e avisa. Pior e a derivada quase nula,')
    print('       que nao avisa e manda o chute para longe. Em')
    print('       x^3 - 2x - 5, a derivada se anula em raiz(2/3) =')
    print('       %.15f; partindo de perto dali:' % np.sqrt(2.0 / 3.0))
    print()
    print('         x0                      f\'(x0)        proximo x')
    for d in (1e-3, 1e-6, 1e-9):
        x0 = np.sqrt(2.0 / 3.0) + d
        print('         %.12f  %12.3e  %15.4e'
              % (x0, fl(x0), x0 - f(x0) / fl(x0)))
    print()
    print('       Com x0 a um bilionesimo do ponto critico, o passo joga')
    print('       o chute para 1e9. Aqui a historia acaba bem, porque a')
    print('       cubica cresce e Newton volta; numa funcao com varias')
    print('       raizes, o salto cai em outra bacia e o metodo converge')
    print('       para a raiz errada sem dizer nada.')
    print()
    print('   (b) Ciclo. A funcao x^3 - 2x + 2 tem um ciclo de periodo 2')
    print('       em Newton: partindo de x0 = 0, o metodo pula entre 0 e')
    print('       1 para sempre.')
    g = lambda x: x ** 3 - 2 * x + 2
    gl = lambda x: 3 * x ** 2 - 2
    h, motivo = newton(g, gl, 0.0, maxit=12)
    print('       motivo da parada: %s' % motivo)
    print('       sequencia: %s' % ', '.join('%.1f' % v for v in h[:9]))
    print('       Nenhum criterio de parada baseado em |x_{n+1} - x_n|')
    print('       detecta isso, porque a diferenca nao diminui nunca. E')
    print('       o ciclo e exato, e nao aproximado: 0 e 1 se mapeiam um')
    print('       no outro em aritmetica exata e em ponto flutuante.')
    print()
    print('   (c) Divergencia: o chute inicial fora da bacia de atracao.')
    print('       A funcao atan(x) tem raiz unica em zero e e o exemplo')
    print('       mais limpo disso.')
    print()
    at = np.arctan
    atl = lambda x: 1.0 / (1.0 + x * x)
    # o limiar e a orbita de periodo 2: -x = x - (1+x^2) atan(x),
    # isto e, atan(x) = 2x/(1+x^2). Medido, e nao citado.
    limiar = brentq(lambda x: np.arctan(x) - 2 * x / (1 + x * x),
                    0.5, 3.0, xtol=1e-15)
    print('       limiar medido (raiz de atan x = 2x/(1+x^2)): %.10f' % limiar)
    print()
    print('         x0        destino                      |x| final')
    for x0 in (1.0, limiar - 1e-6, limiar + 1e-6, 1.5, 2.0):
        h, motivo = newton(at, atl, x0, maxit=60)
        print('       %9.6f  %-27s  %.3e' % (x0, motivo, abs(h[-1])))
    print()
    print('       Um milionesimo abaixo do limiar converge, um')
    print('       milionesimo acima diverge. O limiar nao tem nada de')
    print('       obvio e nao aparece na funcao: ele e a orbita de')
    print('       periodo 2 do mapa de Newton, onde x vai para -x.')
    print()
    print('       A licao pratica e que Newton precisa de chute bom e de')
    print('       rede de seguranca. A rede padrao e o metodo hibrido,')
    print('       que mantem um intervalo com troca de sinal e so aceita')
    print('       o passo de Newton quando ele cai dentro dele; caso')
    print('       contrario, bissecta. E o que o brentq do SciPy faz.')
    print()
    print('   (d) E a pergunta seguinte: ONDE ficam os chutes ruins?')
    print()
    print('       A intuicao diz que e perto dos pontos criticos, onde a')
    print('       derivada se anula. Medindo em x^3 - 5x, que tem tres')
    print('       raizes reais, -raiz(5), 0 e +raiz(5), e pontos criticos')
    print('       em +-raiz(5/3) = +-1,29099:')
    print()
    R5 = np.sqrt(5.0)
    RC = np.sqrt(5.0 / 3.0)
    raizes3 = [-R5, 0.0, R5]

    def destino(x):
        for _ in range(300):
            d = 3 * x * x - 5
            if d == 0 or not np.isfinite(x):
                return -1
            x = x - (x ** 3 - 5 * x) / d
            if abs(x) > 1e8:
                return -1
        for i, r in enumerate(raizes3):
            if abs(x - r) < 1e-6:
                return i
        return -1

    def trocas(centro, meia, n=4001):
        d = [destino(v) for v in centro + np.linspace(-meia, meia, n)]
        return sum(1 for i in range(1, n) if d[i] != d[i - 1])

    print('       meia-largura   trocas de bacia em torno de:')
    print('                      x = 1,29099 (f\' = 0)     x = 1 ')
    for w in (1e-1, 1e-2, 1e-4, 1e-6, 1e-8, 1e-10):
        print('       %12.0e   %14d %20d'
              % (w, trocas(RC, w), trocas(1.0, w)))
    print()
    print('       Em torno do ponto critico a estrutura PARA. Ate 1e-8')
    print('       sao sempre duas trocas, isto e, tres faixas, e em 1e-10')
    print('       nao sobra troca nenhuma: a janela ja cabe inteira dentro')
    print('       de uma faixa so. Em torno de x = 1 isso nunca acontece,')
    print('       e aparecem seis ou sete trocas em TODAS as escalas, de')
    print('       1e-1 ate 1e-10.')
    print()
    print('       A explicacao esta no mapa de Newton desta cubica,')
    print('       N(x) = 2x^3/(3x^2 - 5):')
    mapa = lambda x: 2 * x ** 3 / (3 * x * x - 5)
    print('         N(1)  = %+.15f' % mapa(1.0))
    print('         N(-1) = %+.15f' % mapa(-1.0))
    hh = 1e-6
    mult = abs((mapa(mapa(1 + hh)) - mapa(mapa(1 - hh))) / (2 * hh))
    print('         multiplicador de (N o N) em 1: %.4f' % mult)
    print()
    print('       O par {1, -1} e uma orbita de periodo 2, e e repelente,')
    print('       porque o multiplicador passa de 1. E sobre ela que as')
    print('       bacias se acumulam.')
    print()
    print('       E o limiar do atan do item (c) era a mesma coisa: a')
    print('       condicao atan(x) = 2x/(1+x^2) e exatamente N(x) = -x,')
    print('       isto e, a orbita de periodo 2 daquele mapa. Os dois')
    print('       exemplos sao o mesmo exemplo. O que estraga Newton nao')
    print('       sao as derivadas nulas, que apenas produzem saltos')
    print('       grandes, e sim as orbitas periodicas repelentes.')
    print()

    print('=' * 72)
    print('4. O CRITERIO DE PARADA QUE ENGANA')
    print('=' * 72)
    print('   Parar quando |f(x)| for pequeno parece razoavel e nao e.')
    print('   O residuo pequeno so garante raiz proxima quando a funcao')
    print('   e ingreme ali; se ela for achatada, f pode ser minusculo')
    print('   longe da raiz.')
    print()
    print('   Exemplo: (x - 1)^8, cuja unica raiz e exatamente 1.')
    print()
    p8 = lambda x: (x - 1.0) ** 8
    print('        x        |x - 1|      f(x)')
    for x in (1.1, 1.05, 1.02, 1.01):
        print('      %5.2f  %11.3e  %11.3e' % (x, abs(x - 1), p8(x)))
    print()
    print('   Em x = 1,05 o residuo ja e 4e-11, que qualquer programa')
    print('   aceitaria como zero, e o erro na raiz ainda e 5 por cento.')
    print('   Com o criterio |f| < 1e-10 o metodo para com dois digitos')
    print('   corretos, achando que tem dez.')
    print()
    print('   O criterio correto mistura os dois, com tolerancia')
    print('   relativa no passo e absoluta de reserva:')
    print()
    print('      parar quando |x_{n+1} - x_n| <= tol_rel*|x_{n+1}| + tol_abs')
    print()
    print('   A parte relativa cuida de raizes grandes, onde exigir erro')
    print('   absoluto de 1e-15 e impossivel; a absoluta cuida de raizes')
    print('   perto de zero, onde o erro relativo nao faz sentido.')
    print()

    print('=' * 72)
    print('5. VAN DER WAALS: O VOLUME MOLAR DO CO2')
    print('=' * 72)
    # constantes do CO2
    a_vdw, b_vdw = 0.3640, 4.267e-5      # Pa m^6/mol^2 e m^3/mol
    T = 300.0
    print('   CO2 a 300 K, com a = %.4f Pa m^6/mol^2 e b = %.3e m^3/mol.'
          % (a_vdw, b_vdw))
    print('   A equacao (p + a/V^2)(V - b) = RT e cubica em V e nao se')
    print('   inverte de cabeca. Resolvendo por Newton, com o gas ideal')
    print('   como chute inicial:')
    print()
    print('      p (bar)   V ideal (L/mol)   V vdW (L/mol)   desvio   iteracoes')
    desvios = {}
    for p_bar in (0.1, 1.0, 10.0, 50.0, 100.0):
        p = p_bar * 1e5
        V_id = R_GAS * T / p
        h, motivo = newton(lambda V: vdw_residuo(V, p, T, a_vdw, b_vdw),
                           lambda V: vdw_derivada(V, p, T, a_vdw, b_vdw),
                           V_id)
        V = h[-1]
        desvios[p_bar] = 100 * (V / V_id - 1)
        print('      %7.1f   %15.6f   %13.6f  %+7.2f%%  %8d'
              % (p_bar, V_id * 1e3, V * 1e3, desvios[p_bar], len(h) - 1))
    print()
    print('   Em 0,1 bar o desvio e de %.2f por cento, e o gas ideal'
          % abs(desvios[0.1]))
    print('   serve. Em 100 bar ele chega a %.0f por cento: o volume real'
          % abs(desvios[100.0]))
    print('   e um terco do que o gas ideal preve, e usar o gas ideal ali')
    print('   nao erraria uma casa decimal, erraria a ordem de grandeza da')
    print('   densidade. A 300 K o CO2 esta abaixo da temperatura critica,')
    print('   de %.0f K, e a 100 bar esta acima da pressao critica, de %.0f'
          % (8 * a_vdw / (27 * R_GAS * b_vdw), a_vdw / (27 * b_vdw ** 2) / 1e5))
    print('   bar: e um fluido supercritico denso, e nada parecido com um gas.')
    print()
    # confere a derivada analitica contra uma diferenca central
    p = 50e5
    V0 = R_GAS * T / p
    hh = V0 * 1e-6
    num = (vdw_residuo(V0 + hh, p, T, a_vdw, b_vdw)
           - vdw_residuo(V0 - hh, p, T, a_vdw, b_vdw)) / (2 * hh)
    ana = vdw_derivada(V0, p, T, a_vdw, b_vdw)
    print('   Conferindo a derivada que foi para o Newton, em V = V_ideal')
    print('   a 50 bar, contra uma diferenca central:')
    print('      analitica:  %.10e' % ana)
    print('      numerica:   %.10e' % num)
    print('      diferenca relativa: %.2e' % abs(num / ana - 1))
    print()
    print('   Essa conferencia deveria ser automatica sempre que se')
    print('   escreve uma derivada a mao para alimentar Newton: e o erro')
    print('   mais comum do metodo, e ele nao se manifesta como erro, e')
    print('   sim como convergencia lenta ou ausente.')
    print()
    # o ponto critico, que tem forma fechada e serve de gabarito
    Tc = 8 * a_vdw / (27 * R_GAS * b_vdw)
    pc = a_vdw / (27 * b_vdw ** 2)
    Vc = 3 * b_vdw
    print('   E o gabarito final. No ponto critico a cubica tem raiz')
    print('   tripla, e vale V_c = 3b exatamente:')
    print('      T_c = %.2f K,  p_c = %.3e Pa' % (Tc, pc))
    print('      V_c previsto (3b):  %.6e m3/mol' % Vc)
    h, motivo = newton(lambda V: vdw_residuo(V, pc, Tc, a_vdw, b_vdw),
                       lambda V: vdw_derivada(V, pc, Tc, a_vdw, b_vdw),
                       Vc * 1.5, maxit=200)
    print('      V_c por Newton:     %.6e m3/mol  (%s, %d iteracoes)'
          % (h[-1], motivo, len(h) - 1))
    print('      erro relativo: %.2e' % abs(h[-1] / Vc - 1))
    print()
    print('   Repare no numero de iteracoes. No ponto critico a raiz e')
    print('   TRIPLA, e ali Newton perde a convergencia quadratica e')
    print('   volta a ser linear, de razao 1 - 1/m = 2/3 para m = 3. Por')
    print('   isso foram %d iteracoes para um problema que longe do ponto'
          % (len(h) - 1))
    print('   critico se resolve em cinco. Raiz multipla e o caso em que')
    print('   Newton deixa de valer a pena sem aviso nenhum.')
    print()


if __name__ == '__main__':
    main()
