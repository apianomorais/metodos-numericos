# -*- coding: utf-8 -*-
"""Matemática simbólica com SymPy, e o projeto que junta as quatro aulas.

O QUE RESOLVE
    1. Deriva automaticamente as fórmulas de erro das aulas 3 e 4, em
       vez de aceitá-las de cabeça, e mostra onde está o termo que
       falta em Simpson.
    2. Mostra que simplificar uma expressão pode destruí-la
       numericamente: o mesmo polinômio, em duas formas algébricas
       idênticas, erra o sinal e dezessete ordens de grandeza.
    3. Mede o custo da ponte entre o simbólico e o numérico, e mostra
       que lambdify entrega o mesmo bit que NumPy escrito à mão.
    4. Exibe três lugares onde o simbólico desiste, e o que fazer em
       cada um.
    5. O projeto: o período do pêndulo de amplitude grande, onde
       aparecem o ponto flutuante da aula 1, as raízes da aula 2, a
       interpolação da aula 3 e a integração da aula 4, num problema só.

A IDEIA
    Algebra simbolica e numerica resolvem problemas diferentes e nao
    competem. O simbolico manipula expressoes: ele deriva, integra,
    expande em serie e resolve equacoes em simbolos, sem nunca
    substituir um numero. O numerico so trabalha com numeros, e e o
    unico que chega a uma resposta quando a expressao nao existe.

    A combinacao util e a de sempre: usar o simbolico para PREPARAR a
    conta e para CONFERIR a resposta, e o numerico para obte-la. Usar
    o simbolico para obter a resposta e lento, e quase sempre
    desnecessario; usar o numerico sem nada para conferir e temerario,
    e e exatamente o que este curso inteiro tentou evitar.

    O pendulo de amplitude grande e o exemplo que fecha o curso porque
    nele as quatro aulas aparecem de uma vez, cada uma no lugar onde e
    indispensavel, e nenhuma delas resolve o problema sozinha.

COMO CONFERIR SE ESTA CERTO
    1. A serie do erro do trapezio tem de comecar em h^3 f''/12 e a de
       Simpson em h^5 f''''/90, com o termo em h^4 AUSENTE. O programa
       imprime as duas series inteiras.
    2. A forma fatorada de (x-1)^8 da o valor certo e a expandida nao;
       as duas sao a mesma expressao, conferida por sympy.simplify.
    3. lambdify tem de bater bit a bit com NumPy escrito a mao
       (rtol=0, atol=0), e ser milhares de vezes mais rapido que subs.
    4. O periodo do pendulo tem referencia independente: a funcao
       ellipk do SciPy, que nao usa nada deste programa.
    5. A serie de SymPy e a integral numerica tem de concordar onde as
       duas valem, e o programa mostra onde cada uma deixa de valer.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import time

import numpy as np
import sympy as sp
from scipy.special import ellipe, ellipk

# SymPy conhece elliptic_k e elliptic_e, mas o lambdify nao sabe sozinho
# que eles vivem em scipy.special: o dicionario abaixo faz a ligacao.
ELIPTICAS = {'elliptic_k': ellipk, 'elliptic_e': ellipe}


# ---------------------------------------------------------------------------
# o pendulo, em simbolos e em numeros
# ---------------------------------------------------------------------------

THETA = sp.symbols('theta_0', positive=True)

# T/T0 = (2/pi) K(sin^2(theta0/2)), com T0 = 2 pi raiz(L/g).
RAZAO_SIM = 2 / sp.pi * sp.elliptic_k(sp.sin(THETA / 2) ** 2)


def razao_exata(t0):
    """T/T0 pela funcao eliptica do SciPy. Referencia independente."""
    return 2 / np.pi * ellipk(np.sin(np.asarray(t0) / 2) ** 2)


def razao_integral(t0, n):
    """T/T0 pelo trapezio na forma de Legendre, com n intervalos.

    A substituicao sen(theta/2) = sen(theta0/2) sen(phi) leva a integral
    singular do pendulo para [0, pi/2] com integrando limitado. E a
    mesma manobra da secao 7 da aula 4, aqui com consequencia fisica.
    """
    k = np.sin(t0 / 2)
    phi = np.linspace(0, np.pi / 2, n + 1)
    y = 1 / np.sqrt(1 - k ** 2 * np.sin(phi) ** 2)
    h = (np.pi / 2) / n
    return 2 / np.pi * h * (y[0] / 2 + y[1:-1].sum() + y[-1] / 2)


def razao_ingenua(t0, n):
    """T/T0 pela integral original, sem substituicao nenhuma.

    O integrando tem 1/raiz na borda, e a unica saida de quem nao
    percebe isso e descartar o ultimo ponto. Serve para medir o estrago.
    """
    th = np.linspace(0, t0, n + 1)[:-1]
    h = t0 / n
    y = 1 / np.sqrt(np.cos(th) - np.cos(t0))
    return np.sqrt(2) / np.pi * h * (y[0] / 2 + y[1:].sum())


def baricentrica(xs, ys, x):
    """Interpolacao de Lagrange na forma baricentrica (aula 3)."""
    n = len(xs)
    w = np.array([1.0 / np.prod([xs[j] - xs[m] for m in range(n) if m != j])
                  for j in range(n)])
    x = np.atleast_1d(np.asarray(x, dtype=float))
    num = np.zeros_like(x)
    den = np.zeros_like(x)
    for j in range(n):
        d = x - xs[j]
        d[d == 0] = 1e-300
        num += w[j] * ys[j] / d
        den += w[j] / d
    r = num / den
    for j in range(n):
        r[x == xs[j]] = ys[j]
    return r


# ---------------------------------------------------------------------------


def main():
    print('=' * 72)
    print('1. AS FORMULAS DE ERRO, DERIVADAS EM TRES LINHAS')
    print('=' * 72)
    u, h = sp.symbols('u h')
    N = 7
    taylor = sum(sp.Symbol('f_%d' % j) * u ** j / sp.factorial(j)
                 for j in range(N))
    print('   Taylor de f em torno de 0, com f_j no lugar de f^(j)(0):')
    print('      ', taylor)
    print()
    erro_t = sp.expand(h / 2 * (taylor.subs(u, 0) + taylor.subs(u, h))
                       - sp.integrate(taylor, (u, 0, h)))
    erro_s = sp.expand(h / 3 * (taylor.subs(u, 0) + 4 * taylor.subs(u, h)
                                + taylor.subs(u, 2 * h))
                       - sp.integrate(taylor, (u, 0, 2 * h)))
    print('   regra menos integral, num painel:')
    print('      trapezio:', erro_t)
    print('      Simpson :', erro_s)
    print()
    print('   Duas coisas para ler nessas duas linhas.')
    print()
    print('   A primeira: o termo dominante do trapezio e f_2 h^3/12 e o')
    print('   de Simpson e f_4 h^5/90, que sao exatamente as formulas da')
    print('   aula 4. Ninguem as digitou aqui; elas saem da subtracao.')
    print()
    print('   A segunda, e mais interessante: a serie de Simpson NAO tem')
    print('   termo em h^4, nem em h^3. Coeficiente de h^3:',
          erro_s.coeff(h, 3), '; de h^4:', erro_s.coeff(h, 4))
    print('   E o "grau que passa de graca" da secao 3 da aula 4, e aqui')
    print('   ele aparece como uma ausencia, que e a forma mais honesta')
    print('   de ve-lo: o cancelamento nao foi suposto, ele sobrou.')
    print()
    print('   A mesma receita resolve a derivada numerica, que o curso so')
    print('   usou de passagem, para conferir a derivada de Newton:')
    f1 = sp.Symbol('f_1')
    prog = sp.expand((taylor.subs(u, h) - taylor.subs(u, 0)) / h - f1)
    cent = sp.expand((taylor.subs(u, h) - taylor.subs(u, -h)) / (2 * h) - f1)
    print('      progressiva menos f_1:', prog)
    print('      central     menos f_1:', cent)
    print('   A progressiva comeca em h, a central comeca em h^2 e so tem')
    print('   potencias pares. O mesmo cancelamento por simetria de')
    print('   Simpson, na derivada: trocar h por -h troca o sinal da')
    print('   formula central, e termos de potencia impar nao sobrevivem')
    print('   a essa troca.')
    print()

    print('=' * 72)
    print('2. SIMPLIFICAR NAO E INOCENTE')
    print('=' * 72)
    x = sp.symbols('x')
    p_fat = (x - 1) ** 8
    p_exp = sp.expand(p_fat)
    print('   As duas expressoes abaixo sao a MESMA funcao:')
    print('      fatorada :', p_fat)
    print('      expandida:', p_exp)
    print('      sympy.simplify(diferenca) =', sp.simplify(p_fat - p_exp))
    print()
    g_fat = sp.lambdify(x, p_fat, 'numpy')
    g_exp = sp.lambdify(x, p_exp, 'numpy')
    print('        x          fatorada        expandida       erro relativo')
    for v in (1.01, 1.001, 1.0001):
        a, b = g_fat(v), g_exp(v)
        print('      %.4f   %.8e   %+.8e   %.1e'
              % (v, a, b, abs(b - a) / a))
    print()
    print('   A coluna da direita nao erra o ultimo digito: ela erra o')
    print('   SINAL e dezessete ordens de grandeza. A forma expandida')
    print('   soma e subtrai parcelas da ordem de 1 para obter um')
    print('   resultado da ordem de 1e-32, e a aula 1 ja disse o que')
    print('   acontece nessa hora.')
    print()
    print('   A licao pratica: expand(), simplify() e together() sao')
    print('   operacoes ALGEBRICAS, e a algebra nao sabe que existe')
    print('   aritmetica de precisao finita. Depois de simplificar,')
    print('   confira numericamente perto dos pontos onde a expressao')
    print('   e pequena.')
    print()

    print('=' * 72)
    print('3. LAMBDIFY: A PONTE, E QUANTO ELA CUSTA')
    print('=' * 72)
    expr = sp.sin(x) * sp.exp(-x ** 2 / 2) + sp.sqrt(1 + x ** 2)
    f_lam = sp.lambdify(x, expr, 'numpy')
    def f_mao(v):
        return np.sin(v) * np.exp(-v ** 2 / 2) + np.sqrt(1 + v ** 2)

    X = np.linspace(0, 3, 200000)
    t0 = time.perf_counter(); f_lam(X); t_lam = time.perf_counter() - t0
    t0 = time.perf_counter(); f_mao(X); t_mao = time.perf_counter() - t0
    amostra = X[:2000]
    t0 = time.perf_counter()
    for v in amostra:
        float(expr.subs(x, float(v)))
    t_subs = (time.perf_counter() - t0) / len(amostra) * len(X)

    print('   Avaliando', len(X), 'pontos de', expr, ':')
    print('      subs + float, um a um : %8.3f s  (extrapolado de 2000)'
          % t_subs)
    print('      lambdify + NumPy      : %8.4f s' % t_lam)
    print('      NumPy escrito a mao   : %8.4f s' % t_mao)
    print('      lambdify e %.0f vezes mais rapido que subs.'
          % (t_subs / t_lam))
    print('      (os tempos variam com a maquina; a razao, pouco)')
    print()
    iguais = np.array_equal(f_lam(X), f_mao(X))
    print('   lambdify bate bit a bit com o NumPy escrito a mao?', iguais)
    print('   (comparacao exata, nao allclose: nenhum bit de diferenca)')
    print()
    print('   Isso responde a pergunta que sempre aparece. lambdify nao')
    print('   e uma versao lenta do NumPy; ela ESCREVE a funcao NumPy que')
    print('   voce escreveria, e some do caminho. O que e lento e usar')
    print('   subs dentro de um laco, e esse erro custa quatro ordens de')
    print('   grandeza.')
    print()

    print('=' * 72)
    print('4. TRES LUGARES ONDE O SIMBOLICO DESISTE')
    print('=' * 72)
    print('   (a) A equacao que nao tem formula.')
    p5 = x ** 5 - x - 1
    sol = sp.solve(p5, x)
    print('       solve(x^5 - x - 1) devolve', len(sol), 'objetos, e todos')
    print('       sao CRootOf, que quer dizer "a k-esima raiz deste')
    print('       polinomio", e nao uma formula.')
    print('      ', sol[0])
    print('       Nao e limitacao do SymPy: Abel e Ruffini provaram que a')
    print('       formula nao existe. A unica saida e numerica, e e a')
    print('       aula 2:')
    r = 1.2
    for _ in range(30):
        r = r - (r ** 5 - r - 1) / (5 * r ** 4 - 1)
    print('       Newton da     %.12f' % r)
    print('       nroots do SymPy da %.12f'
          % float(sp.Poly(p5, x).nroots(n=15)[0]))
    print('       residuo de Newton: %.1e' % abs(r ** 5 - r - 1))
    print()
    print('   (b) A integral que existe, mas nao ajuda.')
    I1 = sp.integrate(sp.exp(-x ** 2), (x, 0, 1))
    print('       int_0^1 e^{-x^2} dx =', I1)
    print('       O SymPy resolveu, e a resposta e uma funcao especial.')
    print('       Para ter um numero, alguem ainda precisa avaliar erf,')
    print('       o que e feito numericamente. O simbolico aqui nao')
    print('       resolveu o problema, ele deu um nome ao problema.')
    print('       valor: %.15f' % float(I1))
    print()
    print('   (c) A integral que nao existe em forma fechada.')
    alvo = sp.exp(-x ** 2) / (1 + x ** 3)
    I2 = sp.integrate(alvo, (x, 0, 1))
    resolveu = not isinstance(I2, sp.Integral)
    print('       int_0^1 e^{-x^2}/(1+x^3) dx: SymPy resolveu?', resolveu)
    g2 = sp.lambdify(x, alvo, 'numpy')
    no, pe = np.polynomial.legendre.leggauss(20)
    gauss = 0.5 * np.sum(pe * g2(0.5 * no + 0.5))
    print('       Gauss com 20 nos:        %.15f' % gauss)
    print('       evalf do SymPy (20 dig): %.15f'
          % float(sp.Integral(alvo, (x, 0, 1)).evalf(20)))
    print('       diferenca: %.1e' % abs(gauss - float(
        sp.Integral(alvo, (x, 0, 1)).evalf(20))))
    print('       As duas rotas concordam, e nenhuma delas e uma formula.')
    print()

    print('=' * 72)
    print('5. O PROJETO: O PENDULO DE AMPLITUDE GRANDE')
    print('=' * 72)
    print('   Um pendulo simples de comprimento L, solto do repouso com')
    print('   amplitude theta0, tem periodo T. A formula que todo livro')
    print('   traz, T0 = 2 pi raiz(L/g), vale so para theta0 pequeno.')
    print('   A pergunta do projeto e: quanto vale T de verdade?')
    print()
    print('   --- a parte simbolica: a serie ---')
    serie = sp.series(RAZAO_SIM, THETA, 0, 9).removeO()
    serie = sp.expand(serie)
    print('   T/T0 =', serie)
    coefs = [sp.nsimplify(serie.coeff(THETA, j)) for j in (0, 2, 4, 6, 8)]
    print('   coeficientes de theta0^0, ^2, ^4, ^6, ^8:')
    print('     ', coefs)
    print('   O 1/16 e o resultado classico: o periodo cresce com a')
    print('   amplitude, e cresce quadraticamente para comecar.')
    print()

    print('   --- aula 4: a integral, e por que a substituicao importa ---')
    print('   O periodo exato e uma integral que diverge na borda. A')
    print('   substituicao sen(theta/2) = sen(theta0/2) sen(phi) a leva')
    print('   para [0, pi/2] com integrando limitado.')
    print()
    print('      theta0   graus    ingenua, n=512   Legendre, n=8    exato')
    for t0 in (0.5, 1.0, 2.0):
        ex = razao_exata(t0)
        print('      %5.2f  %6.1f    %.8f       %.8f    %.8f'
              % (t0, np.degrees(t0), razao_ingenua(t0, 512),
                 razao_integral(t0, 8), ex))
    print()
    print('   Oito pontos na forma certa batem quinhentos e doze na')
    print('   forma errada, e nao e por pouco. A forma ingenua converge')
    print('   como raiz de h:')
    t0 = 1.0
    ex = razao_exata(t0)
    ant = None
    print('           n      ingenua       erro      razao de erros')
    for n in (32, 128, 512, 2048):
        e = abs(razao_ingenua(t0, n) - ex)
        print('        %5d   %.8f   %.2e   %s'
              % (n, razao_ingenua(t0, n), e,
                 '—' if ant is None else '%.3f' % (ant / e)))
        ant = e
    print('   A razao de erros da 2 quando n quadruplica, ou seja, o')
    print('   erro cai como n^(-1/2). Para um digito a mais sao cem')
    print('   vezes mais pontos.')
    print()
    print('   E a forma de Legendre? Ela nao e so melhor, ela e exata:')
    print()
    print('      theta0  graus    n=8       n=16      n=32      n=64')
    for t0 in (0.5, 1.0, 2.0, 2.5, 3.0, 3.10):
        ex = razao_exata(t0)
        e = [abs(razao_integral(t0, n) - ex) for n in (8, 16, 32, 64)]
        print('      %5.2f %6.1f  ' % (t0, np.degrees(t0))
              + '  '.join('%.2e' % v for v in e))
    print()
    print('   Ate uns 115 graus o trapezio com OITO intervalos ja esta no')
    print('   ultimo bit. E o mesmo Euler-Maclaurin da secao 7 da aula 4:')
    print('   o integrando e par nas duas pontas, todas as derivadas de')
    print('   ordem impar se anulam la, e a convergencia vira geometrica.')
    print('   Acima de 170 graus a magica acaba, porque k se aproxima de')
    print('   1 e o integrando quase estoura em phi = pi/2. Isso tem')
    print('   sentido fisico: o periodo diverge na posicao invertida.')
    print()

    print('   --- aula 1: o cancelamento para amplitude pequena ---')
    print('   Quanto o periodo cresce em relacao ao caso ideal? Essa')
    print('   pergunta pede T/T0 - 1, e e uma subtracao de dois numeros')
    print('   proximos de 1.')
    print()
    ser_pequena = (lambda v: v ** 2 / 16 + 11 * v ** 4 / 3072
                   + 173 * v ** 6 / 737280)
    print('      theta0      (2/pi)K - 1          serie           relativo')
    for t0 in (1e-2, 1e-4, 1e-6, 1e-7, 1e-8):
        a = razao_exata(t0) - 1.0
        b = ser_pequena(t0)
        print('      %7.0e   %.14e   %.14e   %.1e'
              % (t0, a, b, abs(a - b) / b))
    print()
    print('   Em theta0 = 1e-8 a subtracao direta devolve ZERO, e a')
    print('   resposta certa e 6,25e-18. Nao ha nada de errado com a')
    print('   funcao eliptica: o erro esta em pedir a diferenca de dois')
    print('   numeros que coincidem nos dezesseis digitos. A serie nao')
    print('   subtrai nada e por isso acerta.')
    print()
    print('   O mesmo acontece com a DERIVADA, e vale ver, porque e')
    print('   contraintuitivo: a formula simbolica exata e pior que a')
    print('   serie truncada.')
    dR = sp.diff(RAZAO_SIM, THETA)
    f_dR = sp.lambdify(THETA, dR, [ELIPTICAS, 'numpy'])
    ser_d = (lambda v: v / 8 + 11 * v ** 3 / 768 + 173 * v ** 5 / 122880)
    print('      dR/dtheta0 =', dR)
    print()
    print('   (a serie so vale como referencia para theta0 pequeno, e e')
    print('   nessa faixa que a comparacao abaixo esta feita)')
    print()
    print('      theta0    formula exata        serie         relativo')
    for t0 in (1e-8, 1e-7, 1e-6, 1e-4, 1e-2):
        a = float(f_dR(t0))
        b = ser_d(t0)
        print('      %7.0e   %.12e   %.12e   %.1e'
              % (t0, a, b, abs(a - b) / b))
    print()
    print('   A formula exata contem E(k) - cos^2(theta0/2) K(k), e esses')
    print('   dois termos coincidem em treze digitos quando theta0 e')
    print('   1e-6. Exata em algebra nao quer dizer exata em float64.')
    print()

    print('   --- aula 2: inverter a relacao ---')
    print('   A pergunta de laboratorio e a inversa: medi T/T0, qual era')
    print('   a amplitude? Newton, com a derivada que o SymPy forneceu.')
    print()
    f_R = sp.lambdify(THETA, RAZAO_SIM, [ELIPTICAS, 'numpy'])
    print('      T/T0 alvo   theta0 (rad)    graus     passos  '
          'volta por trapezio   erro')
    for alvo in (1.05, 1.20, 2.00):
        v, passos = 1.0, 0
        while passos < 60:
            fv = float(f_R(v)) - alvo
            vn = v - fv / float(f_dR(v))
            passos += 1
            if abs(vn - v) < 1e-15:
                v = vn
                break
            v = vn
        volta = razao_integral(v, 64)
        print('      %8.2f    %.12f  %9.6f  %4d     %.12f    %.1e'
              % (alvo, v, np.degrees(v), passos, volta, abs(volta - alvo)))
    print()
    print('   A coluna da volta nao usa o SymPy: ela refaz a integral')
    print('   pelo trapezio na forma de Legendre, que e outro caminho')
    print('   inteiro. As duas rotas fecham no ultimo bit, e e isso que')
    print('   autoriza confiar no resultado.')
    print()

    print('   --- aula 3: a tabela de consulta ---')
    print('   Cada avaliacao de K custa caro. Para um ajuste de dados com')
    print('   milhares de chamadas, compensa interpolar uma vez e')
    print('   consultar depois. Em [0, 3] rad, erro maximo em 1001 alvos:')
    print()
    alvos = np.linspace(0, 3, 1001)
    ex = razao_exata(alvos)
    print('         n    igualmente espacados    Chebyshev     ganho')
    for n in (5, 9, 13, 17, 21, 25):
        xi = np.linspace(0, 3, n)
        xc = np.sort(1.5 + 1.5 * np.cos((2 * np.arange(n) + 1)
                                        * np.pi / (2 * n)))
        ei = np.max(np.abs(baricentrica(xi, razao_exata(xi), alvos) - ex))
        ec = np.max(np.abs(baricentrica(xc, razao_exata(xc), alvos) - ex))
        print('        %3d        %.3e           %.3e     %5.0f x'
              % (n, ei, ec, ei / ec))
    print()
    print('   Chebyshev ganha, e o ganho CRESCE com n, que e a assinatura')
    print('   da aula 3. Mas repare que nenhuma das duas colunas despenca')
    print('   como no exemplo de Runge: as duas convergem devagar. A')
    print('   razao e fisica. A funcao T/T0 tem uma singularidade')
    print('   logaritmica em theta0 = pi, logo ali fora do intervalo, e')
    print('   polinomio nenhum se aproxima rapido de uma funcao com')
    print('   singularidade perto do intervalo. Para chegar perto de pi')
    print('   o caminho e outro: interpolar em log(pi - theta0).')
    print()

    print('   --- o fechamento ---')
    print('   Uma pergunta de fisica de primeiro periodo, "quanto vale o')
    print('   periodo de um pendulo", consumiu as quatro aulas:')
    print('     aula 4  para calcular a integral, e a substituicao decide')
    print('             entre oito pontos e meio milhao;')
    print('     aula 1  para descobrir que T/T0 - 1 nao se calcula por')
    print('             subtracao quando a amplitude e pequena;')
    print('     aula 2  para inverter a relacao e responder a pergunta')
    print('             que o laboratorio realmente faz;')
    print('     aula 3  para transformar a resposta cara numa tabela')
    print('             barata, e para saber por que ela converge devagar;')
    print('     aula 5  para obter a serie, a derivada e o valor de')
    print('             referencia sem erro algebrico de ninguem.')
    print()
    print('   Nenhuma delas resolveria o problema sozinha. E assim que')
    print('   metodos numericos aparecem na pratica: nunca um de cada')
    print('   vez, e sempre com a fisica dizendo onde o metodo vai')
    print('   falhar antes de ele falhar.')
    print()


if __name__ == '__main__':
    main()
