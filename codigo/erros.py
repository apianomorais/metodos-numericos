# -*- coding: utf-8 -*-
"""Erros numéricos: de onde vêm, como se propagam, e quantos dígitos sobram.

O QUE RESOLVE
    1. Mede a propagação do erro pelas operações aritméticas e compara a
       cota de pior caso com o que de fato acontece, por Monte Carlo.
    2. Aplica a fórmula de propagação por funções a um caso de
       laboratório, e confere a linearização contra o cálculo direto nos
       extremos.
    3. Calcula o número de condição de problemas conhecidos e mostra que
       ele prevê a perda de dígitos antes de qualquer conta.
    4. Separa condicionamento de problema de estabilidade de algoritmo,
       com um exemplo de cada, incluindo a matriz de Hilbert.
    5. Mede o h ótimo da derivada numérica, nas versões progressiva e
       central, e confere contra raiz(eps) e eps^(1/3).

A IDEIA
    Todo resultado numerico carrega erro de tres origens, e vale separa-las
    porque o que se faz contra cada uma e diferente. O erro dos DADOS vem
    de fora e nao se conserta por dentro: um comprimento medido com regua
    traz a incerteza da regua. O erro de TRUNCAMENTO vem de trocar um
    processo infinito por um finito, e existiria mesmo numa maquina de
    precisao infinita; e o unico que se reduz refinando. O erro de
    ARREDONDAMENTO vem da aritmetica de precisao finita, e existiria mesmo
    com um metodo exato.

    Os dois ultimos puxam em sentidos opostos, e e dai que sai o resultado
    mais util da aula: refinar melhora ate certo ponto e piora depois.

    A segunda ideia e o numero de condicao. Ele mede quanto o problema
    amplifica erro relativo, e nao depende do algoritmo: e propriedade do
    problema. A estabilidade, que e propriedade do algoritmo, diz se ele
    acrescenta erro alem disso. Um algoritmo estavel num problema mal
    condicionado da resposta ruim, e a culpa nao e dele.

COMO CONFERIR SE ESTA CERTO
    1. A cota de pior caso tem de ser, por construcao, maior que qualquer
       erro observado; o programa roda 200 mil amostras e verifica.
    2. A propagacao linearizada tem de bater com o calculo direto nos
       extremos do intervalo, e bate em seis casas no exemplo do pendulo.
    3. O erro medido na matriz de Hilbert tem de ficar ABAIXO de
       kappa vezes eps, que e cota superior e nao igualdade.
    4. O h otimo medido tem de cair perto de raiz(eps) para a diferenca
       progressiva e de eps^(1/3) para a central.
    5. O numero de condicao de uma soma, Soma|x_i| / |Soma x_i|, tem de
       reproduzir a amplificacao do erro relativo medida diretamente.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import math

import numpy as np


# ---------------------------------------------------------------------------


def condicao_soma(xs):
    """kappa de uma soma: quanto ela amplifica o erro relativo das parcelas."""
    s = sum(xs)
    if s == 0:
        return float('inf')
    return sum(abs(x) for x in xs) / abs(s)


def condicao_funcao(f, x, rel=1e-6):
    """kappa = |x f'(x) / f(x)|, com f' por diferenca central.

    O passo e RELATIVO a x. Com passo absoluto, em x = 1e8 o h caberia
    em poucos espacamentos da grade e a derivada sairia com ruido: o
    kappa da raiz quadrada dava 0,4911 em vez de 0,5.
    """
    h = rel * max(1.0, abs(x))
    d = (f(x + h) - f(x - h)) / (2 * h)
    return abs(x * d / f(x))


# ---------------------------------------------------------------------------


def main():
    eps = np.finfo(float).eps

    print('=' * 72)
    print('1. PROPAGACAO PELAS OPERACOES, E O PRECO DO PIOR CASO')
    print('=' * 72)
    print('   Na soma e na subtracao os erros ABSOLUTOS se somam; na')
    print('   multiplicacao e na divisao, os RELATIVOS. As duas sao cotas')
    print('   de pior caso: supoem que todos os erros conspiram.')
    print()
    x, dx = 12.345, 0.005
    y, dy = 12.289, 0.005
    print('   O exemplo que importa: x = %.3f +- %.3f, y = %.3f +- %.3f'
          % (x, dx, y, dy))
    print('      erro relativo de entrada: %.2e e %.2e' % (dx / x, dy / y))
    d = x - y
    dd = dx + dy
    print('      x - y = %.3f +- %.3f' % (d, dd))
    print('      erro relativo da saida:   %.4f, ou seja, %.1f%%'
          % (dd / d, 100 * dd / d))
    print('      amplificacao: %.1f vezes' % ((dd / d) / (dx / x)))
    print()
    k = condicao_soma([x, -y])
    print('   O numero de condicao da soma, Soma|x_i| / |Soma x_i|, vale')
    print('   %.1f, e ele PREVE essa amplificacao: %.2e vezes %.1f = %.4f,'
          % (k, dx / x, k, (dx / x) * k))
    print('   contra os %.4f medidos. A formula e a medida sao a mesma coisa.'
          % (dd / d))
    print()
    print('   Nenhum digito foi perdido na subtracao, que e exata. O que a')
    print('   conta revelou e que a diferenca ja carregava pouca informacao.')
    print()
    print('   kappa de algumas somas:')
    print('      parcelas                      soma         kappa      digitos')
    for c in ([1.0, 1.0, 1.0], [1e8, 1.0, -1e8], [1.0, -0.9999999],
              [12.345, -12.289], [1.0, 1e-20]):
        kk = condicao_soma(c)
        print('      %-28s  %-11.4g  %-10.4g %4.1f'
              % (str(c)[:28], sum(c), kk, math.log10(kk) if kk > 0 else 0))
    print()

    print('   Mas a cota de pior caso cobra caro. Somando n parcelas com')
    print('   erros independentes, ela supoe que todos apontam para o mesmo')
    print('   lado, e isso praticamente nunca acontece. Por Monte Carlo,')
    print('   com 200 mil amostras de erros uniformes em [-1, 1]:')
    print()
    print('        n    cota de pior caso   desvio tipico   pior observado   razao')
    rng = np.random.default_rng(7)
    for n in (2, 4, 10, 100):
        a = rng.uniform(-1, 1, size=(200000, n)).sum(axis=1)
        pior = float(n)
        assert np.abs(a).max() <= pior, 'a cota foi violada'
        print('      %4d   %14.1f    %13.3f   %14.3f   %5.1f'
              % (n, pior, a.std(), np.abs(a).max(), pior / a.std()))
    print()
    print('   A cota nunca e violada, como tem de ser, e para n = 100 ela')
    print('   e 17 vezes maior que o desvio tipico e quase 4 vezes maior')
    print('   que o pior caso observado em duzentas mil tentativas.')
    print()
    print('   Dai vem a diferenca de convencao entre o laboratorio e o')
    print('   calculo numerico. No laboratorio, erros independentes se')
    print('   combinam em quadratura, raiz(soma dos quadrados), que e a')
    print('   previsao estatistica honesta. No calculo numerico a cota')
    print('   garantida e preferida, porque ali o erro nao e aleatorio:')
    print('   ele e determinado pelo algoritmo, e pode muito bem conspirar.')
    print()

    print('=' * 72)
    print('2. PROPAGACAO POR FUNCOES: O PENDULO')
    print('=' * 72)
    print('   Para y = f(x), a expansao de Taylor de primeira ordem da')
    print('   dy = |f\'(x)| dx. Com varias variaveis, somam-se as parciais.')
    print()
    L, dL, g, dg = 1.000, 0.002, 9.78, 0.01
    T = 2 * np.pi * np.sqrt(L / g)
    dT = T / 2 * (dL / L + dg / g)
    print('   T = 2 pi raiz(L/g), com L = %.3f +- %.3f m e g = %.2f +- %.2f m/s2'
          % (L, dL, g, dg))
    print('      T  = %.6f s' % T)
    print('      dT = (T/2)(dL/L + dg/g) = %.6f s' % dT)
    print('      T  = (%.3f +- %.3f) s' % (T, dT))
    print()
    cantos = [2 * np.pi * np.sqrt(Lv / gv)
              for Lv in (L - dL, L + dL) for gv in (g - dg, g + dg)]
    meia = (max(cantos) - min(cantos)) / 2
    print('   Conferindo sem linearizar, avaliando nos quatro cantos:')
    print('      menor %.6f s, maior %.6f s, meia largura %.6f s'
          % (min(cantos), max(cantos), meia))
    print('      a formula linearizada deu %.6f s' % dT)
    print('      diferenca relativa: %.2e' % (abs(meia - dT) / meia))
    print()
    print('   A linearizacao acerta em seis casas porque as incertezas sao')
    print('   pequenas diante dos valores. Com incertezas grandes ela')
    print('   deixa de valer, e ai o caminho e avaliar nos extremos ou')
    print('   fazer Monte Carlo.')
    print()
    print('   A forma em erros relativos e mais util para decidir onde')
    print('   gastar o esforco de medicao:')
    print('      ER_T = (1/2) ER_L + (1/2) ER_g = %.6f' % ((dL / L + dg / g) / 2))
    print('      medido:                          %.6f' % (dT / T))
    print()
    print('   REGRA DAS POTENCIAS: para y = c x1^a1 x2^a2 ..., os erros')
    print('   relativos entram pesados pelos EXPOENTES. Em T, as potencias')
    print('   sao 1/2 e -1/2, e por isso os dois pesos sao 1/2. Em E = mv^2/2')
    print('   o peso de v e 2: medir a velocidade com o dobro de cuidado')
    print('   vale mais que medir a massa.')
    print()
    print('   Contribuicao de cada grandeza para o erro de T:')
    print('      de L: %.6f s  (%.0f%% do total)'
          % (T / 2 * dL / L, 100 * (dL / L) / (dL / L + dg / g)))
    print('      de g: %.6f s  (%.0f%% do total)'
          % (T / 2 * dg / g, 100 * (dg / g) / (dL / L + dg / g)))
    print('   Medir L melhor e o que compensa, e a conta diz isso antes de')
    print('   voltar ao laboratorio.')
    print()

    print('=' * 72)
    print('3. O NUMERO DE CONDICAO, E QUANTOS DIGITOS SOBRAM')
    print('=' * 72)
    print('   kappa = |x f\'(x) / f(x)| mede a amplificacao do erro')
    print('   relativo. Ele e propriedade do PROBLEMA.')
    print()
    print('      funcao            x          kappa      digitos perdidos')
    casos = [('raiz(x)', np.sqrt, 2.0), ('raiz(x)', np.sqrt, 1e8),
             ('exp(x)', np.exp, 1.0), ('exp(x)', np.exp, 30.0),
             ('log(x)', np.log, 1.001), ('tan(x)', np.tan, 1.0),
             ('tan(x)', np.tan, 1.5), ('tan(x)', np.tan, 1.5707)]
    for nome, f, xv in casos:
        kk = condicao_funcao(f, xv)
        print('      %-12s %10.6g  %12.4g       %5.1f'
              % (nome, xv, kk, max(0.0, math.log10(kk))))
    print()
    print('   A raiz quadrada da 1/2 em qualquer x: ela AMORTECE erro, e e')
    print('   sempre bem condicionada. A exponencial em x = 30 amplifica')
    print('   por 30. E a tangente perto de pi/2 amplifica por milhoes:')
    print('   mudar o argumento na sexta casa muda a resposta em ordens de')
    print('   grandeza, e nenhum algoritmo evita isso.')
    print()
    print('   A regra que sai dai, e que deveria ser feita ANTES de rodar:')
    print()
    print('        kappa      digitos perdidos   sobram de 16')
    for kk in (1e2, 1e4, 1e8, 1e12, 1e16, 1e18):
        perd = math.log10(kk)
        print('      %9.0e  %16.0f  %13s'
              % (kk, perd, '%.0f' % max(0, 16 - perd) if perd < 16 else 'nenhum'))
    print()

    print('=' * 72)
    print('4. PROBLEMA MAL POSTO CONTRA ALGORITMO INSTAVEL')
    print('=' * 72)
    print('   Caso A: problema BEM condicionado, algoritmo INSTAVEL.')
    print('   A raiz pequena de x^2 + bx + 1 = 0 vale cerca de -1/b, de')
    print('   modo que kappa = |b/(-1/b)| |dx/db| = |b^2| |1/b^2| = 1.')
    print('   O problema nao tem dificuldade nenhuma; a formula de Bhaskara')
    print('   direta e que estraga a conta, e a aula 2 mostrou isso.')
    print('   Conserto: trocar de formula. Custa tres linhas.')
    print()
    print('   Caso B: problema MAL condicionado, algoritmo ESTAVEL.')
    print('   A matriz de Hilbert, H_ij = 1/(i+j-1), que e exatamente a')
    print('   matriz das equacoes normais do ajuste polinomial na base das')
    print('   potencias, e o assunto da aula 9.')
    print()
    print('        n      kappa(H)      erro medido    kappa*eps     razao')
    for n in (4, 6, 8, 10, 12):
        H = np.array([[1.0 / (i + j + 1) for j in range(n)] for i in range(n)])
        xv = np.ones(n)
        b = H @ xv
        xc = np.linalg.solve(H, b)
        kk = np.linalg.cond(H)
        err = np.linalg.norm(xc - xv) / np.linalg.norm(xv)
        print('      %3d   %.3e     %.2e      %.2e     %.3f'
              % (n, kk, err, kk * eps, err / (kk * eps)))
    print()
    print('   A ultima coluna fica entre 0,004 e 0,04: o erro medido e uma')
    print('   a duas ordens ABAIXO do limite, como tem de ser, porque')
    print('   kappa*eps e cota superior. O que interessa e que o erro')
    print('   cresce junto com kappa, decada por decada.')
    print()
    print('   Em n = 12 o numero de condicao passa de 1/eps, e nao sobra')
    print('   digito nenhum. A eliminacao de Gauss com pivotamento do')
    print('   LAPACK, que o numpy chama, e dos algoritmos mais estaveis que')
    print('   existem: nao ha o que trocar. A saida e MUDAR O PROBLEMA, e')
    print('   no ajuste polinomial isso se faz trocando a base das')
    print('   potencias por uma base ortogonal.')
    print()

    print('=' * 72)
    print('5. O DILEMA: TRUNCAMENTO CONTRA ARREDONDAMENTO')
    print('=' * 72)
    print('   A derivada numerica poe os dois erros em disputa direta.')
    print('   O truncamento cai com h; o arredondamento cresce com 1/h,')
    print('   porque o numerador e uma subtracao de quase iguais.')
    print()
    x0 = 1.0
    exato = np.cos(x0)
    print('      Derivada de sen(x) em x = 1, exata = %.16f' % exato)
    print()
    print('         h        progressiva      erro      central        erro')
    melhor_p = melhor_c = None
    for k in range(1, 17):
        h = 10.0 ** -k
        ap = (np.sin(x0 + h) - np.sin(x0)) / h
        ac = (np.sin(x0 + h) - np.sin(x0 - h)) / (2 * h)
        ep, ec = abs(ap - exato), abs(ac - exato)
        if melhor_p is None or ep < melhor_p[0]:
            melhor_p = (ep, h)
        if melhor_c is None or ec < melhor_c[0]:
            melhor_c = (ec, h)
        print('      1e-%02d   %12.9f  %.2e  %12.9f  %.2e' % (k, ap, ep, ac, ec))
    print()
    print('   melhor h da progressiva: %.0e, erro %.2e'
          % (melhor_p[1], melhor_p[0]))
    print('      previsto raiz(eps) = %.3e' % math.sqrt(eps))
    print('   melhor h da central    : %.0e, erro %.2e'
          % (melhor_c[1], melhor_c[0]))
    print('      previsto eps^(1/3) = %.3e' % eps ** (1 / 3))
    print()
    print('   As duas previsoes acertam a ordem de grandeza, e a diferenca')
    print('   entre elas e o ponto. Na progressiva, truncamento ~ h e')
    print('   arredondamento ~ eps/h, e igualar os dois da h ~ raiz(eps).')
    print('   Na central o truncamento cai mais rapido, ~ h^2, e igualar')
    print('   h^2 com eps/h da h ~ eps^(1/3), que e MIL VEZES maior.')
    print()
    print('   O resultado pratico: a diferenca central nao so e mais')
    print('   precisa no melhor h, ela chega a %.0f vezes menos erro,'
          % (melhor_p[0] / melhor_c[0]))
    print('   como atinge esse melhor com um h bem mais confortavel.')
    print()
    print('   E a licao que vale para o curso inteiro: existe um h otimo, e')
    print('   pedir mais precisao refinando alem dele PIORA o resultado.')
    print('   O mesmo padrao vai reaparecer na integracao numerica, com o')
    print('   mesmo formato de V no grafico log-log.')
    print()


if __name__ == '__main__':
    main()
