# -*- coding: utf-8 -*-
"""O que a máquina pode e o que ela não pode representar.

O QUE RESOLVE
    1. Mede o épsilon da máquina em vez de citá-lo, e mostra onde ficam
       os buracos da reta de ponto flutuante.
    2. Demonstra que a soma de ponto flutuante não é associativa, e mede
       o quanto a ordem das parcelas muda o resultado.
    3. Exibe o cancelamento catastrófico em duas fórmulas algebricamente
       idênticas, e mostra qual delas usar.
    4. Separa condicionamento de problema de estabilidade de algoritmo,
       que são coisas diferentes e costumam ser confundidas.
    5. Mede o número de condição de uma matriz e mostra que ele prevê,
       com antecedência, quantos dígitos a solução vai perder.

A IDEIA
    Um numero de ponto flutuante de 64 bits gasta 1 bit no sinal, 11 no
    expoente e 52 na mantissa. A consequencia imediata e que os numeros
    representaveis nao estao igualmente espacados: entre 1 e 2 eles
    distam 2^-52, entre 2 e 4 distam 2^-51, e assim por diante, dobrando
    a cada potencia de dois. A reta real e representada por uma grade
    que fica mais grossa conforme se afasta da origem.

    Dai saem todos os fenomenos desta aula. A soma nao e associativa
    porque cada soma parcial e arredondada para a grade local, e a grade
    de (a+b) nao e a mesma de (b+c). O cancelamento e catastrofico
    porque subtrair dois numeros proximos nao cria erro nenhum, mas
    REVELA o erro relativo que ja estava la: os digitos bons se cancelam
    e os ruins sobem para o topo.

    A distincao final e a mais importante da aula. Condicionamento e
    propriedade do PROBLEMA: diz o quanto a resposta muda quando o dado
    muda, e nenhum algoritmo conserta um problema mal condicionado.
    Estabilidade e propriedade do ALGORITMO: diz se ele acrescenta erro
    ao que o problema ja tinha. Um algoritmo estavel num problema mal
    condicionado da uma resposta ruim, e a culpa nao e dele.

COMO CONFERIR SE ESTA CERTO
    1. O epsilon medido tem de dar 2^-52, e sys.float_info.epsilon
       tem de concordar.
    2. A diferenca entre as duas ordens de soma tem de ser da ordem de
       n vezes o epsilon vezes a maior parcela.
    3. As duas formulas da equacao do segundo grau tem de concordar
       quando nao ha cancelamento e divergir quando ha, e a formula
       estavel tem de bater com a de precisao arbitraria.
    4. O erro relativo da solucao do sistema tem de ser limitado pelo
       numero de condicao vezes o epsilon.
    5. Cada afirmacao de perda de digitos e conferida contra o resultado
       exato obtido com a biblioteca de precisao arbitraria.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import math
import sys
from decimal import Decimal, getcontext

import numpy as np


# ---------------------------------------------------------------------------
# 1. a grade de ponto flutuante
# ---------------------------------------------------------------------------


def epsilon_medido():
    """O menor e tal que 1 + e ainda difere de 1, achado por bisseção."""
    e = 1.0
    while 1.0 + e / 2.0 != 1.0:
        e = e / 2.0
    return e


def espacamento(x):
    """A distância até o próximo float depois de x."""
    return np.nextafter(x, np.inf) - x


# ---------------------------------------------------------------------------
# 2. soma
# ---------------------------------------------------------------------------


def soma_kahan(v):
    """Soma compensada: carrega o erro de uma parcela para a seguinte.

    A variável c guarda o pedaço que foi perdido no arredondamento da
    soma anterior, e o subtrai da parcela seguinte. O efeito é que o
    erro deixa de crescer com n e passa a ser praticamente constante.
    """
    s = 0.0
    c = 0.0
    for x in v:
        y = x - c
        t = s + y
        c = (t - s) - y
        s = t
    return s


# ---------------------------------------------------------------------------
# 3. cancelamento
# ---------------------------------------------------------------------------


def raizes_ingenua(a, b, c):
    """A fórmula do colégio, aplicada aos dois sinais."""
    d = np.sqrt(b * b - 4 * a * c)
    return (-b + d) / (2 * a), (-b - d) / (2 * a)


def raizes_estavel(a, b, c):
    """A mesma equação, sem subtrair números próximos.

    Quando b é grande e positivo, -b + sqrt(b^2-4ac) subtrai dois
    números quase iguais. A saída é calcular primeiro a raiz em que os
    sinais SOMAM, e obter a outra do produto das raízes, que vale c/a.
    """
    d = np.sqrt(b * b - 4 * a * c)
    q = -0.5 * (b + np.sign(b) * d) if b != 0 else -0.5 * d
    return q / a, c / q


def raizes_exatas(a, b, c, digitos=50):
    """As mesmas raízes com precisão arbitrária, para servir de gabarito."""
    getcontext().prec = digitos
    A, B, C = Decimal(a), Decimal(b), Decimal(c)
    d = (B * B - 4 * A * C).sqrt()
    return (-B + d) / (2 * A), (-B - d) / (2 * A)


# ---------------------------------------------------------------------------
# 4 e 5. condicionamento
# ---------------------------------------------------------------------------


def hilbert(n):
    """A matriz de Hilbert, H_ij = 1/(i+j-1): o exemplo clássico de
    matriz mal condicionada que aparece inocentemente, como matriz das
    equações normais do ajuste polinomial na base das potências."""
    i = np.arange(1, n + 1)
    return 1.0 / (i[:, None] + i[None, :] - 1)


def main():
    print('=' * 72)
    print('1. A GRADE DE PONTO FLUTUANTE NAO E UNIFORME')
    print('=' * 72)
    e = epsilon_medido()
    print('   epsilon medido por bisseccao: %.17e' % e)
    print('   sys.float_info.epsilon:       %.17e' % sys.float_info.epsilon)
    print('   2 elevado a -52:              %.17e' % 2.0 ** -52)
    print('   os tres coincidem: %s' % (e == sys.float_info.epsilon == 2.0 ** -52))
    print()
    print('   O espacamento local da grade, perto de alguns numeros:')
    print()
    print('        x            proximo float - x      em unidades de x')
    for x in (1e-8, 1.0, 2.0, 1e3, 1e8, 1e16, 1e300):
        h = espacamento(x)
        print('      %9.0e    %18.6e   %16.3e' % (x, h, h / x))
    print()
    print('   A ultima coluna e quase constante, e vale cerca de 1,1e-16:')
    print('   o espacamento RELATIVO e que e uniforme, nao o absoluto. Em')
    print('   x = 1e16 o espacamento vale 2, de modo que 1e16 + 1 nao')
    print('   existe e e arredondado de volta para 1e16:')
    print()
    print('      1e16 + 1 == 1e16 ?  %s' % (1e16 + 1 == 1e16))
    print('      1e16 + 2 == 1e16 ?  %s' % (1e16 + 2 == 1e16))
    print()
    print('   E a famosa surpresa do primeiro dia de aula:')
    print()
    print('      0,1 + 0,2 == 0,3 ?  %s' % (0.1 + 0.2 == 0.3))
    print('      0,1 + 0,2 vale      %.20f' % (0.1 + 0.2))
    print('      0,3 vale            %.20f' % 0.3)
    print('      diferenca:          %.3e' % abs(0.1 + 0.2 - 0.3))
    print('      espacamento da grade em 0,3: %.3e' % espacamento(0.3))
    print('      a diferenca e de exatamente %.0f passo da grade'
          % (abs(0.1 + 0.2 - 0.3) / espacamento(0.3)))
    print()
    print('   Nenhum dos tres numeros existe exatamente em binario: 0,1 e')
    print('   uma dizima periodica na base 2, do mesmo modo que 1/3 e')
    print('   dizima na base 10. O computador guarda o float mais proximo,')
    print('   e a soma dos dois mais proximos nao e o mais proximo da soma.')
    print()

    print('=' * 72)
    print('2. A SOMA DE PONTO FLUTUANTE NAO E ASSOCIATIVA')
    print('=' * 72)
    a, b, c = 1e16, -1e16, 1.0
    print('   Com a = 1e16, b = -1e16, c = 1:')
    print('      (a + b) + c = %.1f' % ((a + b) + c))
    print('      a + (b + c) = %.1f' % (a + (b + c)))
    print()
    print('   Nao e sutileza de caso extremo. Um milhao de numeros')
    print('   aleatorios entre 0 e 1, somados de tres maneiras. O gabarito')
    print('   e o math.fsum, que e exatamente arredondado.')
    print()
    rng = np.random.default_rng(7)
    v = rng.random(1000000)
    cres_v = np.sort(v)
    exato = math.fsum(v)

    print('   Primeiro a tentativa obvia, com np.sum:')
    print()
    print('      np.sum crescente:   %.10f   erro %+.3e'
          % (float(np.sum(cres_v)), float(np.sum(cres_v)) - exato))
    print('      np.sum decrescente: %.10f   erro %+.3e'
          % (float(np.sum(cres_v[::-1])), float(np.sum(cres_v[::-1])) - exato))
    print()
    print('   Os dois dao o MESMO numero, e com erro zero. A demonstracao')
    print('   falhou, e a razao vale mais que a demonstracao: o np.sum nao')
    print('   soma da esquerda para a direita. Ele usa soma por pares, que')
    print('   divide o vetor ao meio recursivamente, e cujo erro cresce')
    print('   como log(n) em vez de n. O numpy ja protege quem o usa.')
    print()
    print('   Para ver o efeito e preciso somar a mao, que e o que faz')
    print('   quem escreve o laco em vez de chamar a biblioteca:')
    print()

    def soma_ingenua(w):
        s = 0.0
        for x in w:
            s += x
        return s

    cres = soma_ingenua(cres_v)
    decr = soma_ingenua(cres_v[::-1])
    kah = soma_kahan(cres_v)
    print('      laco, crescente:    %.10f   erro %+.3e' % (cres, cres - exato))
    print('      laco, decrescente:  %.10f   erro %+.3e' % (decr, decr - exato))
    print('      Kahan:              %.10f   erro %+.3e' % (kah, kah - exato))
    print('      np.sum (por pares): %.10f   erro %+.3e'
          % (float(np.sum(cres_v)), float(np.sum(cres_v)) - exato))
    print('      math.fsum (exato):  %.10f' % exato)
    print()
    print('      diferenca entre as duas ordens: %.3e' % abs(cres - decr))
    print('      limite grosseiro, n*eps*soma:   %.3e' % (len(v) * e * exato))
    print()
    print('   Somar do menor para o maior e melhor que o contrario, e a')
    print('   razao e geometrica: enquanto a soma parcial e pequena, a')
    print('   grade local e fina e as parcelas pequenas ainda cabem nela.')
    print('   Somando do maior para o menor, a soma parcial fica grande')
    print('   logo no inicio e as parcelas pequenas caem no vao entre dois')
    print('   floats.')
    print()
    if kah == exato:
        print('   Kahan carrega o erro de cada parcela para a seguinte e,')
        print('   com uma linha a mais de codigo, acerta aqui o mesmo')
        print('   numero que o math.fsum: o erro nao e pequeno, e nulo.')
    else:
        print('   Kahan carrega o erro de cada parcela para a seguinte e')
        print('   erra %.0f vezes menos que o laco crescente, com uma'
              % (abs(cres - exato) / abs(kah - exato)))
        print('   linha a mais de codigo.')
    print('   A licao pratica, porem, nao e implementar Kahan:')
    print('   e usar np.sum e math.fsum, que ja resolvem o problema, e')
    print('   desconfiar de qualquer laco de acumulacao escrito a mao.')
    print()

    print('=' * 72)
    print('3. CANCELAMENTO CATASTROFICO')
    print('=' * 72)
    print('   A equacao x^2 + bx + 1 = 0, com b crescente. As duas raizes')
    print('   sao -b/2 +- sqrt(b^2/4 - 1); quando b cresce, a raiz de')
    print('   menor modulo vem de uma subtracao de numeros quase iguais.')
    print()
    print('        b          ingenua              estavel            '
          'erro ingenua   erro estavel')
    for b in (1e2, 1e4, 1e6, 1e8, 1e10):
        r_ing = raizes_ingenua(1.0, b, 1.0)[0]
        r_est = raizes_estavel(1.0, b, 1.0)
        # a raiz pequena e a de menor modulo em cada par
        pequena_est = min(r_est, key=abs)
        ex = raizes_exatas(1.0, b, 1.0)
        pequena_ex = float(min(ex, key=abs))
        ei = abs(r_ing / pequena_ex - 1) if pequena_ex else float('nan')
        ee = abs(pequena_est / pequena_ex - 1) if pequena_ex else float('nan')
        print('      %7.0e  %20.14e  %20.14e  %8.1e  %12.1e'
              % (b, r_ing, pequena_est, ei, ee))
    print()
    print('   Em b = 1e8 a formula ingenua perde TODOS os digitos: ela da')
    print('   zero, e a raiz verdadeira e -1e-8. A estavel mantem quinze')
    print('   digitos em toda a faixa.')
    print()
    print('   Convem ser preciso sobre o que aconteceu. A subtracao em si')
    print('   e exata: subtrair dois floats proximos nao introduz erro')
    print('   nenhum, e esse e ate um teorema (lema de Sterbenz). O que a')
    print('   subtracao faz e REVELAR o erro que a raiz quadrada ja tinha')
    print('   cometido. Os digitos corretos se cancelam entre si e os')
    print('   digitos de lixo, que estavam no fim, sobem para o comeco.')
    print()
    print('   Por isso a solucao nunca e "calcular com mais cuidado": e')
    print('   reescrever a formula para que a subtracao nao aconteca. A')
    print('   forma estavel calcula a raiz grande, onde os sinais somam, e')
    print('   obtem a pequena pelo produto das raizes, que vale c/a.')
    print()

    print('=' * 72)
    print('4. CONDICIONAMENTO DO PROBLEMA, ESTABILIDADE DO ALGORITMO')
    print('=' * 72)
    print('   Sao duas coisas diferentes, e o exemplo acima so trata da')
    print('   segunda. Para separa-las, a conta de achar a raiz pequena de')
    print('   x^2 + bx + 1 com b = 1e8:')
    print()
    # A perturbacao tem de ser feita em precisao arbitraria. Em float64,
    # 1e8*(1+1e-16) volta a ser exatamente 1e8, porque o espacamento da
    # grade ali e 1,5e-8 e a perturbacao de 1e-8 nao chega a um passo:
    # medir condicionamento com a propria aritmetica que esta sob
    # suspeita nao funciona.
    getcontext().prec = 50
    B = Decimal(10) ** 8
    delta = Decimal(10) ** -16

    def raiz_pequena(Bv):
        d = (Bv * Bv - 4).sqrt()
        return min((-Bv + d) / 2, (-Bv - d) / 2, key=abs)

    ex, exp_ = raiz_pequena(B), raiz_pequena(B * (1 + delta))
    var = abs(exp_ / ex - 1)
    # impressos com 22 digitos a partir do Decimal: em float64 os dois
    # apareceriam identicos, porque diferem so na 17a casa
    # format() com Decimal preserva a precisao; o operador % converteria
    # para float antes de imprimir e apagaria justamente o que interessa
    print('      raiz com b = 1e8:                %s' % format(ex, '.21e'))
    print('      raiz com b perturbado em 1e-16:  %s' % format(exp_, '.21e'))
    print('      variacao relativa da saida:      %.3e' % float(var))
    print('      variacao relativa da entrada:    %.3e' % float(delta))
    print('      numero de condicao do problema:  %.4f' % float(var / delta))
    print()
    print('   A conta fechada confirma: para b grande a raiz pequena vale')
    print('   -1/b, de modo que dx/db = 1/b^2 e o numero de condicao')
    print('   relativo, |(b/x)(dx/db)|, vale exatamente 1.')
    print()
    print('   O problema e BEM condicionado: perturbar o dado em 1e-16')
    print('   muda a resposta em 1e-16. Ele nao tinha nada de dificil. Foi')
    print('   o algoritmo ingenuo que estragou a conta, e por isso ele e')
    print('   chamado de INSTAVEL. Trocando de algoritmo, resolve-se.')
    print()
    print('   Agora um problema que nenhum algoritmo salva. A matriz de')
    print('   Hilbert, H_ij = 1/(i+j-1), resolvendo H x = b com b')
    print('   escolhido para que a resposta seja exatamente (1, 1, ..., 1):')
    print()
    print('        n     cond(H)       erro relativo   cond * eps    razao')
    for n in (4, 6, 8, 10, 12):
        H = hilbert(n)
        x_ex = np.ones(n)
        rhs = H @ x_ex
        x = np.linalg.solve(H, rhs)
        k = np.linalg.cond(H)
        err = np.linalg.norm(x - x_ex) / np.linalg.norm(x_ex)
        prev = k * e
        print('      %3d  %12.3e  %14.3e  %12.3e  %7.3f'
              % (n, k, err, prev, err / prev if prev else float('nan')))
    print()
    print('   A ultima coluna fica entre 0,004 e 0,04, ou seja, o erro')
    print('   medido e uma a duas ordens de grandeza MENOR que o limite.')
    print('   E assim que tem de ser: cond vezes epsilon e um limite')
    print('   superior, e ele seria inutil se fosse atingido sempre. O que')
    print('   interessa e que o erro cresce junto com cond(H), decada por')
    print('   decada, e e por isso que o limite serve para prever.')
    print()
    print('   Em n = 12 o numero de condicao passa de 1e16, que e')
    print('   justamente 1/epsilon, e ai NAO SOBRA DIGITO NENHUM: o erro')
    print('   relativo de 13 por cento quer dizer que a resposta calculada')
    print('   nao tem mais relacao com a correta.')
    print()
    print('   E essencial que o algoritmo usado aqui, a eliminacao de')
    print('   Gauss com pivotamento do LAPACK, e um dos mais estaveis que')
    print('   existem. Ele nao errou: o problema e que esta mal posto.')
    print('   Nenhuma reescrita de formula conserta isso, e a unica saida')
    print('   e mudar o problema, trocando a base das potencias por uma')
    print('   base ortogonal, que e o que a aula 3 faz no ajuste.')
    print()

    print('=' * 72)
    print('5. A REGRA PRATICA QUE SAI DE TUDO ISSO')
    print('=' * 72)
    print('   Digitos perdidos = log10(numero de condicao).')
    print()
    print('        cond        digitos perdidos   sobram de 16')
    for k in (1e2, 1e4, 1e8, 1e12, 1e16, 1e18):
        perd = np.log10(k)
        print('      %9.0e  %16.0f  %13s'
              % (k, perd, '%.0f' % max(0, 16 - perd) if perd < 16 else 'nenhum'))
    print()
    print('   Essa conta deveria ser feita ANTES de rodar o programa, e')
    print('   nao depois de desconfiar do resultado. Ela diz de antemao')
    print('   quantos digitos vao sobrar, e portanto se vale a pena')
    print('   sequer tentar.')
    print()


if __name__ == '__main__':
    main()
