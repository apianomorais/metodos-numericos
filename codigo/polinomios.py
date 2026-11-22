# -*- coding: utf-8 -*-
"""Localizar raízes de polinômios: teoremas que contam sem calcular.

O QUE RESOLVE
    1. Avalia por Horner e mostra que o quociente da divisão por (x-a)
       vem de brinde, o que a aula 8 vai usar.
    2. Compara três cotas clássicas e mostra quanto elas são generosas.
    3. Aplica a regra de sinais de Descartes e mede o quanto ela acerta.
    4. Constrói a sequência de Sturm e confere a contagem EXATA contra
       as raízes conhecidas, em nove intervalos.
    5. Isola todas as raízes automaticamente por bisseção sobre a
       contagem de Sturm, e resolve a quíntica dos pontos de Lagrange.

A IDEIA
    Para uma funcao qualquer, localizar raizes depende de olhar um
    grafico. Para polinomios, nao: existem teoremas que dizem quantas
    raizes reais ha num intervalo SEM calcular nenhuma delas, e a
    localizacao vira um algoritmo mecanico.

    O teorema fundamental da algebra ja da a contabilidade fechada: grau
    n tem n raizes complexas contadas com multiplicidade, e as complexas
    vem em pares conjugados. Se o grau e 5 e achamos tres reais, as duas
    que faltam sao um par complexo, sem discussao.

    Dai em diante os teoremas vao ficando mais fortes e mais caros.
    Descartes custa uma passada pelos coeficientes e da uma cota com
    paridade. Budan-Fourier custa n derivadas e da uma cota por
    intervalo. Sturm custa n divisoes polinomiais e da o numero EXATO.

COMO CONFERIR SE ESTA CERTO
    1. O polinomio de teste tem raizes inteiras conhecidas, -2, -1, 1, 2
       e 3, de modo que toda contagem tem gabarito.
    2. Horner e conferido contra np.polyval e contra a multiplicacao do
       quociente por (x - a).
    3. As cotas tem de conter a maior raiz em modulo, e o programa
       verifica isso com assert.
    4. A contagem de Sturm e comparada com a contagem exata em nove
       intervalos.
    5. As raizes isoladas e refinadas tem de bater com np.roots.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import numpy as np
from scipy.optimize import brentq


# ---------------------------------------------------------------------------


def horner(coefs, x):
    """Avalia p(x) e devolve também o quociente da divisão por (x - x0).

    coefs vai do maior grau para o menor. Custa n multiplicações e n
    somas, contra as 2n da forma ingênua, e de quebra entrega o
    quociente, que é o que a deflação da aula 8 precisa.
    """
    b = [coefs[0]]
    for a in coefs[1:]:
        b.append(a + b[-1] * x)
    return b[-1], b[:-1]


def variacoes(seq):
    """Conta trocas de sinal, ignorando os zeros."""
    s = [np.sign(v) for v in seq if v != 0]
    return sum(1 for i in range(len(s) - 1) if s[i] != s[i + 1])


def cotas(coefs):
    """Cauchy, Lagrange e Laguerre-Thibault, esta só para raízes > 0."""
    a = np.asarray(coefs, dtype=float)
    an, n = a[0], len(a) - 1
    cauchy = 1 + np.max(np.abs(a[1:])) / abs(an)
    lagrange = max(1.0, np.sum(np.abs(a[1:] / an)))
    # o k de Laguerre-Thibault e um GRAU, nao um indice da lista
    negs = [(n - i, v) for i, v in enumerate(a) if v < 0]
    if an > 0 and negs:
        k = max(g for g, _ in negs)
        B = max(abs(v) for _, v in negs)
        lt = 1 + (B / an) ** (1.0 / (n - k)) if n > k else float('inf')
    else:
        lt = float('inf')
    return cauchy, lagrange, lt


def descartes(coefs):
    """Devolve (V(p), V(p(-x))), as cotas para raízes positivas e negativas."""
    n = len(coefs) - 1
    espelho = [v * (-1) ** (n - i) for i, v in enumerate(coefs)]
    return variacoes(coefs), variacoes(espelho)


def sequencia_sturm(coefs):
    """p, p', e os restos com o SINAL TROCADO. É o sinal que faz funcionar."""
    p0 = np.trim_zeros(np.array(coefs, dtype=float), 'f')
    seq = [p0, np.polyder(p0)]
    while len(seq[-1]) > 1:
        _, resto = np.polydiv(seq[-2], seq[-1])
        resto = np.trim_zeros(resto, 'f')
        if resto.size == 0 or np.allclose(resto, 0):
            break
        seq.append(-resto)
    return seq


def conta_sturm(seq, a, b):
    """Número EXATO de raízes reais distintas em (a, b]."""
    V = lambda x: variacoes([np.polyval(s, x) for s in seq])
    return V(a) - V(b)


def isolar(coefs, a, b, minimo=1e-10):
    """Bisseção sobre a CONTAGEM: parte o intervalo até cada pedaço ter
    exatamente uma raiz. É o algoritmo que torna Sturm prático."""
    seq = sequencia_sturm(coefs)
    pilha, prontos = [(a, b)], []
    while pilha:
        aa, bb = pilha.pop()
        n = conta_sturm(seq, aa, bb)
        if n == 0:
            continue
        if n == 1 or bb - aa < minimo:
            prontos.append((aa, bb))
            continue
        m = (aa + bb) / 2
        pilha.append((aa, m))
        pilha.append((m, bb))
    return sorted(prontos)


# ---------------------------------------------------------------------------


def main():
    P = [1, -3, -5, 15, 4, -12]
    EXATAS = [-2, -1, 1, 2, 3]

    print('=' * 72)
    print('1. HORNER: AVALIAR BARATO, E GANHAR O QUOCIENTE')
    print('=' * 72)
    print('   p(x) = x^5 - 3x^4 - 5x^3 + 15x^2 + 4x - 12')
    print('   (as raizes sao -2, -1, 1, 2 e 3, de modo que tudo aqui tem')
    print('    gabarito)')
    print()
    print('   A forma ingenua custa n potencias e n multiplicacoes. Horner')
    print('   reescreve como (((a5 x + a4)x + a3)x + a2)x + ... e custa n')
    print('   multiplicacoes e n somas.')
    print()
    print('        x     Horner      np.polyval    quociente por (x - a)')
    for x in (2, 3, -2, 0, 1.5):
        v, q = horner(P, x)
        ref = np.polyval(P, x)
        assert abs(v - ref) < 1e-10 * max(1, abs(ref))
        print('      %4s  %10.4f  %12.4f    %s'
              % (x, v, ref, ' '.join('%g' % c for c in q)))
    print()
    print('   Conferindo o quociente: multiplicando de volta por (x - 2) e')
    print('   somando o resto, tem de voltar p.')
    v, q = horner(P, 2)
    volta = np.polyadd(np.polymul(q, [1, -2]), [v])
    print('      (x - 2) * quociente + resto = %s'
          % ' '.join('%+g' % c for c in volta))
    print('      p(x)                        = %s'
          % ' '.join('%+g' % c for c in P))
    assert np.allclose(volta, P)
    print('      confere.')
    print()
    print('   Esse quociente nao e subproduto curioso: e a DEFLACAO, e a')
    print('   aula 8 inteira se apoia nele.')
    print()

    print('=' * 72)
    print('2. AS COTAS: ONDE CERTAMENTE NAO HA RAIZ')
    print('=' * 72)
    c, l, lt = cotas(P)
    maior = max(abs(v) for v in EXATAS)
    print('   Cauchy            |x| <  %7.4f' % c)
    print('   Lagrange          |x| <= %7.4f' % l)
    print('   Laguerre-Thibault  x  <  %7.4f   (so para raizes positivas)' % lt)
    print()
    print('   maior raiz em modulo, de verdade: %.4f' % maior)
    assert maior < c and maior <= l
    print('   As tres cotas contem todas as raizes, como tem de ser.')
    print()
    print('   E as tres sao generosas: a melhor delas, %.1f, ainda e %.1f'
          % (min(c, l, lt), min(c, l, lt) / maior))
    print('   vezes maior que a maior raiz. O papel de uma cota nao e dar a')
    print('   resposta: e garantir que a varredura nao deixe raiz de fora.')
    print('   Calcule duas ou tres e fique com a menor.')
    print()
    print('   Para raizes negativas, aplique a mesma cota a p(-x): a menos')
    print('   de sinal, os dois problemas sao o mesmo.')
    print()

    print('=' * 72)
    print('3. DESCARTES: UMA PASSADA PELOS COEFICIENTES')
    print('=' * 72)
    vp, vm = descartes(P)
    pos = sum(1 for v in EXATAS if v > 0)
    neg = sum(1 for v in EXATAS if v < 0)
    print('   coeficientes de p(x) : %s' % P)
    print('   trocas de sinal      : %d' % vp)
    print('   logo n+ e %d, ou %d, ou %d, ...'
          % (vp, vp - 2, max(vp - 4, 0)))
    print('   positivas de verdade : %d' % pos)
    print()
    n = len(P) - 1
    espelho = [v * (-1) ** (n - i) for i, v in enumerate(P)]
    print('   coeficientes de p(-x): %s' % espelho)
    print('   trocas de sinal      : %d' % vm)
    print('   logo n- e %d ou %d' % (vm, vm - 2))
    print('   negativas de verdade : %d' % neg)
    print()
    print('   Aqui Descartes acertou em cheio nos dois casos, e nao e')
    print('   sempre assim. A regra da uma COTA com paridade, e a paridade')
    print('   e metade do valor dela: sabendo que n+ <= 3 e que 3 - n+ e')
    print('   par, so restam 3 e 1, e nunca 2.')
    print()
    print('   O caso em que Descartes e exato sem ambiguidade e V = 0 ou')
    print('   V = 1: ali a cota e a resposta. A quintica da secao 5 e um')
    print('   exemplo.')
    print()

    print('=' * 72)
    print('4. STURM: A CONTAGEM EXATA')
    print('=' * 72)
    seq = sequencia_sturm(P)
    print('   A sequencia e p, p\', e os restos das divisoes sucessivas COM')
    print('   O SINAL TROCADO. E o sinal negativo que faz o teorema valer.')
    print()
    for i, s in enumerate(seq):
        print('      p%d (grau %d): %s'
              % (i, len(s) - 1, ' '.join('%+.4g' % v for v in s)))
    print()
    print('   O numero de raizes reais distintas em (a, b] e V(a) - V(b),')
    print('   onde V conta trocas de sinal na sequencia avaliada no ponto.')
    print()
    print('        intervalo        Sturm    exato')
    erros = 0
    for aa, bb in [(-4, 4), (-4, 0), (0, 4), (-4, -2), (-2, 0),
                   (0, 2), (2, 4), (1.5, 2.5), (0.5, 1.5)]:
        s_ = conta_sturm(seq, aa, bb)
        e_ = sum(1 for v in EXATAS if aa < v <= bb)
        if s_ != e_:
            erros += 1
        print('      (%5.1f, %5.1f]     %4d     %4d  %s'
              % (aa, bb, s_, e_, '' if s_ == e_ else '<-- DIFERE'))
    print()
    print('   %d discordancia(s) em 9 intervalos.' % erros)
    print()
    print('   Duas restricoes, e vale conhece-las. O polinomio precisa ser')
    print('   livre de raizes multiplas, o que se resolve dividindo p pelo')
    print('   mdc(p, p\'). E a conta exige divisoes polinomiais sucessivas,')
    print('   que em ponto flutuante podem degenerar para grau alto. Para')
    print('   grau moderado, Sturm e imbativel.')
    print()
    print('   Com Sturm, isolar vira algoritmo: parta o intervalo ao meio e')
    print('   siga pelos pedacos que ainda contem raiz, ate cada pedaco ter')
    print('   exatamente uma.')
    print()
    caixas = isolar(P, -5, 5)
    print('      %d intervalos isolados, um por raiz:' % len(caixas))
    achadas = []
    for aa, bb in caixas:
        try:
            r = brentq(lambda x: np.polyval(P, x), aa, bb, xtol=1e-14)
        except ValueError:
            r = (aa + bb) / 2        # a raiz esta na borda do intervalo
        achadas.append(r)
        print('        (%9.6f, %9.6f]  ->  %12.9f' % (aa, bb, r))
    print()
    ref = np.sort(np.roots(P))
    print('      np.roots, para comparar: %s'
          % ' '.join('%.9f' % v.real for v in ref))
    print('      maior diferenca: %.2e'
          % max(abs(a - b.real) for a, b in zip(sorted(achadas), ref)))
    print()

    print('=' * 72)
    print('5. OS PONTOS DE LAGRANGE')
    print('=' * 72)
    print('   No problema restrito de tres corpos, as cinco posicoes de')
    print('   equilibrio no referencial girante sao os pontos de Lagrange.')
    print('   Os tres colineares saem de quinticas.')
    print()
    print('   Para L1, entre os dois corpos, a distancia adimensional r ao')
    print('   corpo menor satisfaz')
    print()
    print('      r^5 - (3-mu) r^4 + (3-2mu) r^3 - mu r^2 + 2 mu r - mu = 0')
    print()
    mu = 3.0034e-6
    L1 = [1, -(3 - mu), (3 - 2 * mu), -mu, 2 * mu, -mu]
    print('   Para o sistema Sol-Terra, mu = %.4e.' % mu)
    print()
    vp, vm = descartes(L1)
    print('   Etapa 1, Descartes: V(p) = %d, V(p(-x)) = %d.' % (vp, vm))
    print('      As negativas estao resolvidas: V = 0 quer dizer NENHUMA')
    print('      raiz negativa, sem ambiguidade. Para as positivas sobra')
    print('      "5, 3 ou 1", que nao serve.')
    print()
    s1 = sequencia_sturm(L1)
    print('   Etapa 2, Sturm:')
    for aa, bb in [(-4, 0), (0, 1), (1, 4), (0, 0.02), (0.005, 0.02)]:
        print('      raizes em (%-6g, %-5g]: %d'
              % (aa, bb, conta_sturm(s1, aa, bb)))
    print('      Uma so, e ela esta entre 0,005 e 0,02. A ambiguidade de')
    print('      Descartes some.')
    print()
    print('   Etapa 3, refinar:')
    r1 = brentq(lambda x: np.polyval(L1, x), 0.005, 0.02, xtol=1e-15)
    hill = (mu / 3) ** (1 / 3)
    d = 1.496e8
    print('      r(L1)         = %.10f  ->  %s km da Terra'
          % (r1, format(int(r1 * d), ',d').replace(',', ' ')))
    print('      raio de Hill  = %.10f  ->  %s km'
          % (hill, format(int(hill * d), ',d').replace(',', ' ')))
    print('      a aproximacao classica erra %.3f%%'
          % (100 * abs(hill - r1) / r1))
    print()
    L2 = [1, (3 - mu), (3 - 2 * mu), -mu, -2 * mu, -mu]
    r2 = brentq(lambda x: np.polyval(L2, x), 0.005, 0.02, xtol=1e-15)
    print('      r(L2)         = %.10f  ->  %s km da Terra'
          % (r2, format(int(r2 * d), ',d').replace(',', ' ')))
    print()
    print('   Conferindo contra np.roots, que usa autovalores da matriz')
    print('   companheira e nao sabe nada de Sturm:')
    todas = np.roots(L1)
    reais = [v.real for v in todas if abs(v.imag) < 1e-9]
    print('      reais: %s' % ' '.join('%.10f' % v for v in reais))
    print('      complexas: %d, em %d par(es) conjugado(s)'
          % (len(todas) - len(reais), (len(todas) - len(reais)) // 2))
    assert abs(reais[0] - r1) < 1e-12
    print('      diferenca para a nossa: %.2e' % abs(reais[0] - r1))
    print()
    print('   O SOHO observa o Sol do L1 e o telescopio James Webb orbita o')
    print('   L2, os dois a cerca de um milhao e meio de quilometros da')
    print('   Terra. A conta que poe um telescopio no lugar certo e esta.')
    print()


if __name__ == '__main__':
    main()
