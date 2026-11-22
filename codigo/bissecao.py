# -*- coding: utf-8 -*-
"""O método da bisseção: lento, infalível, e com erro garantido de antemão.

O QUE RESOLVE
    1. Testa o teorema de Bolzano e as suas duas ressalvas, que são onde
       o método falha: função descontínua e raiz de multiplicidade par.
    2. Isola as raízes antes de refinar, e mostra o que a varredura
       deixa passar quando a malha é grossa demais.
    3. Confere a previsão de quantas iterações serão gastas, que é a
       propriedade que nenhum outro método desta unidade oferece.
    4. Compara os três critérios de parada, e mede onde o laço para
       sozinho por falta de números representáveis.
    5. Resolve a equação de Wien e mede a temperatura da fotosfera
       solar, comparando bisseção com a brentq do SciPy.

A IDEIA
    Se f e continua em [a,b] e troca de sinal nas pontas, o teorema do
    valor intermediario garante que existe raiz dentro. A bissecao usa
    essa garantia e so ela: corta o intervalo ao meio, olha o SINAL do
    ponto medio, e fica com a metade que ainda troca de sinal.

    Repare no que o metodo joga fora. Ele nunca olha o VALOR de f, so o
    sinal. Se f(x) vale 1e-9 estamos quase certamente perto da raiz, e a
    bissecao trata esse caso igual a f(x) = 1e6. Dai a sua lentidao, e
    dai tambem a sua robustez: sem usar derivada nem suavidade, nao ha
    hipotese que possa ser violada.

    O preco e conhecido com exatidao antes de comecar. Depois de k
    passos o intervalo mede (b-a)/2^k, e isso NAO DEPENDE DA FUNCAO.
    Nenhum dos metodos das proximas aulas pode prometer o mesmo.

COMO CONFERIR SE ESTA CERTO
    1. O numero de iteracoes medido tem de bater com log2((b-a)/tol),
       e o programa compara os dois em tres casos.
    2. A raiz encontrada tem de coincidir com a da brentq do SciPy, que
       e outro algoritmo.
    3. Nos dois contraexemplos de Bolzano o programa mostra o que de
       fato acontece, em vez de afirmar que daria errado.
    4. O passo em que o laco trava tem de ser log2 da largura inicial
       dividida pelo espacamento local da grade, e e.
    5. A constante de Wien obtida tem de bater com a do CODATA.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import math

import numpy as np
from scipy.constants import c, h
from scipy.constants import k as k_B
from scipy.optimize import bisect, brentq


# ---------------------------------------------------------------------------


def bissecao(f, a, b, tol=1e-12, nmax=200, historico=None):
    """Bisseção com os três critérios de parada e teto de iterações.

    Devolve (raiz, iteracoes, motivo). O motivo diz qual criterio parou
    o laco, o que e mais util do que parecer: um laco que sempre para
    pelo teto esta mal configurado.
    """
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError('f(a) e f(b) tem o mesmo sinal: Bolzano nao se aplica')
    for k in range(1, nmax + 1):
        x = (a + b) / 2
        fx = f(x)
        if historico is not None:
            historico.append((k, a, b, x, fx, b - a))
        if x == a or x == b:
            return x, k, 'a grade acabou'
        if fx == 0.0:
            return x, k, 'raiz exata'
        if fa * fx < 0:
            b, fb = x, fx
        else:
            a, fa = x, fx
        # o teste vem DEPOIS de cortar, para que a contagem bata com
        # ceil(log2((b-a)/tol)); testando antes, o laco gasta um passo a mais
        if b - a < tol:
            return (a + b) / 2, k, 'intervalo < tol'
    return (a + b) / 2, nmax, 'teto de iteracoes'


def localizar(f, a, b, n=100):
    """Varre [a,b] e devolve (trocas de sinal, nos onde f da zero).

    O segundo retorno existe porque uma raiz que cai EXATAMENTE num no da
    malha nao produz troca de sinal: o produto y[i]*y[i+1] vale zero, e
    nao e negativo. Sem esse ramo a varredura perde a raiz justamente no
    caso em que a encontrou de primeira.
    """
    x = np.linspace(a, b, n + 1)
    y = f(x)
    trocas = [(x[i], x[i + 1]) for i in range(n) if y[i] * y[i + 1] < 0]
    exatas = [x[i] for i in range(n + 1) if y[i] == 0.0]
    return trocas, exatas


# ---------------------------------------------------------------------------


def main():
    print('=' * 72)
    print('1. BOLZANO, E AS DUAS VEZES EM QUE ELE NAO SE APLICA')
    print('=' * 72)
    print('   Se f e continua em [a,b] e f(a)f(b) < 0, existe raiz dentro.')
    print('   As duas hipoteses importam, e os contraexemplos sao estes:')
    print()
    print('   (a) f(x) = 1/x em [-1, 1]. O teste de sinal PASSA:')
    print('       f(-1) = %.1f, f(1) = %.1f, produto %.1f < 0.'
          % (-1.0, 1.0, -1.0))
    print('       E nao ha raiz nenhuma: o que existe ali e um polo.')
    a, b = -1.0, 1.0
    x = (a + b) / 2
    print('       Rodando a bissecao, o primeiro ponto medio ja e x = %.1f,' % x)
    print('       e 1/x estoura na primeira avaliacao. O metodo nao devolve')
    print('       resposta errada: ele quebra, que e o melhor dos dois.')
    print()
    print('   (b) f(x) = x^2 em [-1, 1]. Existe raiz, em x = 0, e o teste')
    print('       de sinal FALHA: f(-1)f(1) = %.0f > 0.' % 1.0)
    print('       Raiz de multiplicidade par nao troca o sinal da funcao,')
    print('       e a bissecao nao tem como encontra-la. O mesmo vale para')
    print('       multiplicidade 4, 6, e assim por diante.')
    print()
    print('   A licao: o teste de sinal nao e nem necessario nem suficiente.')
    print('   Ele e suficiente QUANDO a funcao e continua, e nunca e')
    print('   necessario. Um esboco do grafico continua sendo o melhor')
    print('   investimento de tempo antes de qualquer conta.')
    print()

    print('=' * 72)
    print('2. ISOLAR ANTES DE REFINAR')
    print('=' * 72)
    f = lambda x: x ** 3 - 9 * x + 3
    print('   f(x) = x^3 - 9x + 3 tem tres raizes reais. Varrendo [-5, 5]:')
    print()
    for n in (6, 10, 50):
        ints, _ = localizar(f, -5, 5, n)
        print('      com %2d subintervalos: %d trocas de sinal  %s'
              % (n, len(ints), ['[%.2f, %.2f]' % t for t in ints]))
    print()
    exatas = np.sort(np.roots([1, 0, -9, 3]))
    print('   As tres raizes, pelo companheiro de matriz do numpy:')
    print('      ', ' '.join('%.8f' % r for r in exatas))
    print()
    print('   Agora os dois casos que a varredura NAO ve.')
    print()
    print('   (a) Duas raizes dentro do mesmo subintervalo.')
    print('       g(x) = (x - 1)(x - 1,013), com as raizes a 0,013 de')
    print('       distancia uma da outra:')
    g = lambda x: (x - 1) * (x - 1.013)
    for n in (10, 100, 150, 200, 1000):
        ints, ex = localizar(g, 0, 2, n)
        print('          %4d subintervalos (passo %.4f): %d troca(s)'
              % (n, 2.0 / n, len(ints)))
    print('       A funcao entra e sai do eixo dentro do mesmo pedaco, e o')
    print('       sinal nas pontas nao muda. Nenhum aviso e emitido: a')
    print('       varredura simplesmente nao reporta nada.')
    print()
    print('   (b) A raiz EXATAMENTE num no da malha.')
    print('       h(x) = x - 0,5 varrida em [0, 1]:')
    hh = lambda x: x - 0.5
    for n in (10, 11):
        ints, ex = localizar(hh, 0, 1, n)
        print('          %2d subintervalos: %d troca(s) de sinal, %d no(s) com'
              ' f = 0 exato %s' % (n, len(ints), len(ex),
                                   ['%.4f' % v for v in ex]))
    print('       Com n par o 0,5 e um no, o produto da zero e nao e')
    print('       negativo, e o teste de troca de sinal perde a raiz')
    print('       justamente por te-la acertado em cheio. Por isso a')
    print('       varredura precisa do ramo de igualdade, e nao so do')
    print('       produto negativo.')
    print()

    print('=' * 72)
    print('3. O ALGORITMO, E O ERRO QUE SE SABE DE ANTEMAO')
    print('=' * 72)
    print('   Depois de k passos o intervalo mede (b-a)/2^k, e a raiz esta')
    print('   dentro. Entao o erro do ponto medio e no maximo metade disso,')
    print('   e isso NAO DEPENDE DA FUNCAO.')
    print()
    print('   Em [0, 1], os cinco primeiros passos de x^3 - 9x + 3:')
    print()
    print('        k        a         b         x        f(x)      b - a')
    hist = []
    bissecao(f, 0.0, 1.0, tol=1e-12, nmax=5, historico=hist)
    for k, aa, bb, xx, fx, larg in hist:
        print('        %d   %8.5f  %8.5f  %8.5f  %+9.5f  %8.5f'
              % (k, aa, bb, xx, fx, larg))
    print()
    r_ex = brentq(f, 0, 1, xtol=1e-15)
    print('   Depois de quatro iteracoes a raiz esta em [0,31250; 0,37500],')
    print('   o ponto medio vale 0,34375 e o erro maximo e 0,03125.')
    print('   A raiz, com muitas iteracoes, vale %.8f.' % r_ex)
    print()
    print('   A contagem prevista contra a medida:')
    print()
    print('      funcao          intervalo         tol    previsto  medido')
    wien = lambda x: (x - 5) * np.exp(x) + 5
    expo = lambda x: np.exp(x) - 2
    for nome, fun, a0, b0, tol in [
            ('x^3-9x+3', f, 0.0, 1.0, 1e-6),
            ('x^3-9x+3', f, 0.0, 1.0, 1e-12),
            ('Wien', wien, 4.0, 6.0, 1e-12),
            ('e^x - 2', expo, 0.0, 2.0, 1e-12),
            ('e^x - 2', expo, -1000.0, 2.0, 1e-12)]:
        prev = math.ceil(math.log2((b0 - a0) / tol))
        _, k, _ = bissecao(fun, a0, b0, tol=tol)
        print('      %-14s [%7.1f, %5.1f]  %.0e    %5d    %4d'
              % (nome, a0, b0, tol, prev, k))
    print()
    print('   Cada iteracao ganha log10(2) = %.4f casa decimal, ou seja,'
          % math.log10(2))
    print('   sao %.2f iteracoes por casa. E o intervalo inicial quase nao'
          % (1 / math.log10(2)))
    print('   importa, e as duas ultimas linhas mostram isso: o intervalo')
    print('   passou de 2 para 1002, 501 vezes maior, e o custo subiu em')
    print('   %.0f iteracoes, que e log2(501) = %.1f.'
          % (math.ceil(math.log2(1002 / 1e-12)) - math.ceil(math.log2(2 / 1e-12)),
             math.log2(501)))
    print()

    print('=' * 72)
    print('4. OS CRITERIOS DE PARADA, E ONDE O LACO TRAVA')
    print('=' * 72)
    print('   Tres candidatos, e nenhum serve sozinho:')
    print('      1. |b - a| < eps          (largura do intervalo)')
    print('      2. |b - a|/|x| < eps      (largura relativa)')
    print('      3. |f(x)| < delta         (residuo)')
    print()
    print('   O residuo sozinho engana nas duas direcoes. Em f = (x-1)^7:')
    print()
    print('        x        |x - raiz|      |f(x)|')
    for xv in (1.1, 1.05, 1.01):
        print('      %5.2f     %.4f        %.3e' % (xv, abs(xv - 1), (xv - 1) ** 7))
    print()
    print('   Em x = 1,1 o residuo vale 1e-7 e o erro vale 0,1: um criterio')
    print('   de residuo com delta = 1e-6 pararia aqui, com UM digito')
    print('   correto, convencido de ter dezesseis.')
    print()
    print('   E engana tambem na direcao oposta. Em f(x) = 1e8 (x - 1):')
    print()
    print('        x              |x - raiz|      |f(x)|')
    for dx in (1e-10, 1e-13, 1e-15):
        print('      1 + %.0e        %.0e        %.3e' % (dx, dx, 1e8 * dx))
    print()
    print('   Em x = 1 + 1e-13 a raiz ja esta certa ate o decimo terceiro')
    print('   digito, e o residuo ainda vale 1e-5: um criterio com')
    print('   delta = 1e-9 recusaria parar, e ficaria rodando atras de uma')
    print('   precisao que a maquina nao tem.')
    print()
    print('   E ha um limite que nao se negocia. Pedir tol = 1e-20 em')
    print('   float64 e pedir o impossivel, e o laco rodaria para sempre.')
    print('   O criterio honesto e parar quando o ponto medio deixa de se')
    print('   mover, porque ali a grade acabou:')
    print()
    hist = []
    r, k, motivo = bissecao(f, 0.0, 1.0, tol=1e-30, historico=hist)
    larg = hist[-1][5]
    print('      partindo de [0, 1] com tol = 1e-30:')
    print('         parou em %d passos, motivo: %s' % (k, motivo))
    print('         raiz    = %.17f' % r)
    print('         residuo = %.3e' % f(r))
    print('         largura final        = %.3e' % larg)
    print('         espacamento da grade = %.3e' % np.spacing(r))
    print('         log2(1 / espacamento) = %.1f' % math.log2(1 / np.spacing(r)))
    print()
    print('   Foram %d cortes ate o ponto medio travar, detectados no passo'
          % (k - 1))
    print('   %d, e log2(1/espacamento) vale %.0f: o numero de cortes e'
          % (k, math.log2(1 / np.spacing(r))))
    print('   exatamente log2 da largura inicial dividida pelo espacamento')
    print('   local da grade. O criterio')
    print('   x == a or x == b nao depende de tolerancia nenhuma, e por')
    print('   isso e o unico que nunca trava o programa.')
    print()

    print('=' * 72)
    print('5. WIEN, E A TEMPERATURA DO SOL')
    print('=' * 72)
    print('   Derivando a lei de Planck em lambda e igualando a zero, com')
    print('   x = hc/(lambda kB T), sobra a equacao transcendental')
    print()
    print('        (x - 5) e^x + 5 = 0')
    print()
    w = lambda x: (x - 5) * np.exp(x) + 5
    print('   Alem da raiz trivial x = 0, ha uma perto de 5. Isolando:')
    print('      g(4) = %.4f, g(6) = %.4f: sinais opostos.' % (w(4), w(6)))
    print()
    xw, kw, mot = bissecao(w, 4.0, 6.0, tol=1e-12)
    xb = brentq(w, 4, 6, xtol=1e-15)
    print('      bissecao: x = %.9f em %d iteracoes' % (xw, kw))
    print('      brentq  : x = %.9f' % xb)
    print('      diferenca: %.2e' % abs(xw - xb))
    print()
    bw = h * c / (xw * k_B)
    bc = 2.897771955e-3
    print('      b = hc/(x kB) = %.9e m K' % bw)
    print('      CODATA 2022   = %.9e m K' % bc)
    print('      diferenca relativa: %.1e' % (abs(bw - bc) / bc))
    print()
    lam = 502e-9
    print('   O pico solar medido fica em %.0f nm. Logo' % (lam * 1e9))
    print('      T = b / lambda_max = %.0f K' % (bw / lam))
    print()
    print('   Partindo da lei de Planck e de um metodo de 1817, mede-se a')
    print('   temperatura da fotosfera solar sem sair do laboratorio de')
    print('   informatica. O valor aceito e 5772 K.')
    print()
    print('   Quanto custa cada metodo, em avaliacoes da funcao:')
    print()
    print('      funcao                   bisect   brentq   razao')
    for nome, fn, a0, b0 in [('x^3 - 9x + 3', f, 0.0, 1.0),
                             ('Wien', w, 4.0, 6.0),
                             ('cos x - x', lambda x: np.cos(x) - x, 0.0, 2.0),
                             ('x^10 - 1', lambda x: x ** 10 - 1, 0.3, 1.21)]:
        r1, i1 = bisect(fn, a0, b0, xtol=1e-12, full_output=True)
        r2, i2 = brentq(fn, a0, b0, xtol=1e-12, full_output=True)
        assert abs(r1 - r2) < 1e-9, nome
        print('      %-22s   %4d     %4d    %5.1f'
              % (nome, i1.function_calls, i2.function_calls,
                 i1.function_calls / i2.function_calls))
    print()
    print('   A brentq resolve com quatro a cinco vezes menos avaliacoes, e')
    print('   mantem a garantia da bissecao, porque so aceita o passo rapido')
    print('   quando ele cai dentro do intervalo que ainda troca de sinal.')
    print('   Em trabalho de pesquisa, use brentq.')
    print()
    print('   Vale um caso curioso. Em x^10 - 1 no intervalo [0,5; 1,3] a')
    print('   bissecao ganha de lavada:')
    r1, i1 = bisect(lambda x: x ** 10 - 1, 0.5, 1.3, xtol=1e-12,
                    full_output=True)
    r2, i2 = brentq(lambda x: x ** 10 - 1, 0.5, 1.3, xtol=1e-12,
                    full_output=True)
    print('      bisect %d avaliacoes, brentq %d.'
          % (i1.function_calls, i2.function_calls))
    print('   Os pontos medios sao 0,9 depois 1,1 depois 1,0, e o terceiro')
    print('   cai EXATAMENTE na raiz. E sorte do intervalo escolhido, e nao')
    print('   propriedade do metodo; mudando para [0,3; 1,21] a bissecao')
    print('   volta a gastar %d avaliacoes. Serve de aviso contra tirar'
          % bisect(lambda x: x ** 10 - 1, 0.3, 1.21, xtol=1e-12,
                   full_output=True)[1].function_calls)
    print('   conclusao de uma medida so.')
    print()


if __name__ == '__main__':
    main()
