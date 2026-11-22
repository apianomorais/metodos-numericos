# -*- coding: utf-8 -*-
"""Sistemas de numeração: conversão entre bases, e por que 0,1 não é exato.

O QUE RESOLVE
    1. Converte nos dois sentidos, entre bases quaisquer, e confere cada
       conversão por três rotas independentes.
    2. Decide, antes de converter, se a conversão vai terminar: o critério
       é um teorema sobre fatores primos, e o programa o testa em dezenas
       de casos.
    3. Prevê o tamanho do período da dízima, quando ela é infinita, e
       compara a previsão com o período medido.
    4. Abre o número 0,1 em 53 bits e mostra exatamente quanto ele vale.
    5. Refaz a conta do erro que derrubou um míssil Patriot em 1991, e
       descobre, no caminho, que acrescentar bits nem sempre adianta.

A IDEIA
    Um sistema posicional de base beta escreve qualquer numero como soma
    de potencias de beta. A base 10 nao tem nada de especial: so herdamos
    dez dedos. O computador usa base 2 porque um circuito distingue dois
    estados com folga e dez com dificuldade.

    A troca de base e exata para inteiros e pode nao ser para fracoes, e
    e dai que vem todo o resto do curso. Uma fracao p/q tem representacao
    FINITA na base beta exatamente quando todo fator primo de q (ja na
    forma irredutivel) divide beta. Em base 10, q = 10 tem fatores 2 e 5,
    os dois dividem 10, e 1/10 e finita. Em base 2, o fator 5 nao divide
    2, e 1/10 vira dizima.

    Nao ha nada de errado com o binario. Em base 3, 1/3 e finita e 1/2
    nao e. O que existe e uma incompatibilidade entre a base que a pessoa
    usa para escrever e a base que a maquina usa para guardar.

COMO CONFERIR SE ESTA CERTO
    1. Toda conversao e conferida pela volta (converter e desconverter tem
       de devolver o numero original) e contra as funcoes prontas bin,
       oct e hex do Python, que nao participam do calculo.
    2. O criterio de finitude e testado contra a conversao real: o
       programa converte e verifica se terminou, em 48 pares de fracao e
       base.
    3. O periodo previsto pela ordem multiplicativa e comparado com o
       periodo medido na expansao, digito a digito.
    4. O valor de 0,1 em 53 bits e obtido por Fraction, que e aritmetica
       exata de inteiros, e nao por ponto flutuante.
    5. A conta do Patriot bate com o valor publicado no relatorio do GAO,
       0,34 s apos cem horas.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import math
import struct
from fractions import Fraction

SIMBOLOS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'


# ---------------------------------------------------------------------------
# as conversoes, escritas como se faz na mao
# ---------------------------------------------------------------------------


def para_decimal(texto, base):
    """Valor posicional: soma cada digito vezes a potencia da posicao."""
    if '.' in texto:
        inteiro, frac = texto.split('.')
    else:
        inteiro, frac = texto, ''
    v = Fraction(0)
    for i, d in enumerate(reversed(inteiro)):
        v += SIMBOLOS.index(d.upper()) * Fraction(base) ** i
    for i, d in enumerate(frac):
        v += SIMBOLOS.index(d.upper()) * Fraction(1, base ** (i + 1))
    return v


def inteiro_para_base(n, base, passos=None):
    """Divisoes sucessivas: o resto de cada divisao e um digito, de tras
    para a frente. Se passos for uma lista, ela recebe a conta inteira."""
    if n == 0:
        return '0'
    d = []
    while n > 0:
        q, r = divmod(n, base)
        if passos is not None:
            passos.append((n, q, r))
        d.append(SIMBOLOS[r])
        n = q
    return ''.join(reversed(d))


def fracao_para_base(f, base, maximo=60, passos=None):
    """Multiplicacoes sucessivas, com deteccao de periodo.

    Guardar a fracao EXATA (e nao um float) permite reconhecer quando um
    resto ja apareceu, e e assim que o periodo e medido em vez de
    adivinhado.
    """
    vistos = {}
    digitos = []
    x = Fraction(f)
    while x != 0 and len(digitos) < maximo:
        if x in vistos:
            inicio = vistos[x]
            return ''.join(digitos), inicio, len(digitos) - inicio
        vistos[x] = len(digitos)
        y = x * base
        d = int(y)
        if passos is not None:
            passos.append((x, y, d))
        digitos.append(SIMBOLOS[d])
        x = y - d
    return ''.join(digitos), None, 0


def digitos_brutos(f, base, quantos):
    """Expansao sem parar no periodo, para quando se quer ver os digitos."""
    x, d = Fraction(f), []
    for _ in range(quantos):
        x *= base
        k = int(x)
        d.append(SIMBOLOS[k])
        x -= k
    return ''.join(d)


def finita(f, base):
    """Teorema: p/q irredutivel e finita na base beta se e somente se todo
    fator primo de q divide beta."""
    q = Fraction(f).denominator
    for p in range(2, base + 1):
        if base % p == 0:
            while q % p == 0:
                q //= p
    return q == 1


def periodo_previsto(f, base):
    """O periodo e a ordem multiplicativa de beta modulo q, depois de
    retirar de q os fatores que ele tem em comum com beta."""
    q = Fraction(f).denominator
    while True:
        g = math.gcd(q, base)
        if g == 1:
            break
        q //= g
    if q == 1:
        return 0
    k, r = 1, base % q
    while r != 1:
        r = r * base % q
        k += 1
    return k


# ---------------------------------------------------------------------------


def main():
    print('=' * 72)
    print('1. CONVERTER, E CONFERIR POR TRES ROTAS')
    print('=' * 72)
    print('   Divisoes sucessivas para ir, valor posicional para voltar, e')
    print('   as funcoes prontas do Python como terceira testemunha.')
    print()
    print('        n        base   resultado     volta      bin/oct/hex')
    prontas = {2: lambda n: bin(n)[2:], 8: lambda n: oct(n)[2:],
               16: lambda n: hex(n)[2:].upper()}
    falhas = 0
    for n in (13, 100, 255, 4095, 1000000):
        for base in (2, 7, 8, 16):
            meu = inteiro_para_base(n, base)
            volta = int(para_decimal(meu, base))
            pronta = prontas[base](n) if base in prontas else '(so a volta)'
            ok = (volta == n) and (pronta == '—' or pronta == meu)
            if not ok:
                falhas += 1
            print('      %7d    %2d   %-12s  %7d    %s  %s'
                  % (n, base, meu, volta, pronta, 'ok' if ok else 'FALHOU'))
    print()
    print('   %d conversoes, %d falha(s).' % (20, falhas))
    print()
    print('   A conta de 13 para binario, passo a passo:')
    passos = []
    r = inteiro_para_base(13, 2, passos)
    for n, q, resto in passos:
        print('      %2d / 2 = %2d, resto %d' % (n, q, resto))
    print('      lendo os restos de baixo para cima: %s' % r)
    print()

    print('=' * 72)
    print('2. A CONVERSAO VAI TERMINAR? O CRITERIO E UM TEOREMA')
    print('=' * 72)
    print('   p/q irredutivel e finita na base beta se e somente se todo')
    print('   fator primo de q divide beta. O programa testa a previsao')
    print('   convertendo de verdade e vendo se a conta termina.')
    print()
    print('      fracao                 base 2      base 3      base 10     base 16')
    casos = [(1, 2), (1, 3), (1, 5), (1, 10), (3, 4), (1, 7), (2, 5), (15, 32),
             (1, 6), (1, 9), (7, 8), (1, 100)]
    erros = 0
    for p, q in casos:
        f = Fraction(p, q)
        linha = '      %-22s' % ('%d/%d' % (p, q))
        for base in (2, 3, 10, 16):
            prev = finita(f, base)
            _, inicio, _ = fracao_para_base(f, base, maximo=400)
            medido = (inicio is None)
            if prev != medido:
                erros += 1
            linha += '%-12s' % ('finita' if prev else 'dizima')
        print(linha)
    print()
    print('   %d pares testados, %d discordancia(s) entre previsao e medida.'
          % (len(casos) * 4, erros))
    print()
    print('   Repare na linha de 1/3: dizima em base 2 e em base 10, finita')
    print('   em base 3. E na de 1/2: finita em 2, 10 e 16, dizima em base 3.')
    print('   Nao e o binario que tem defeito, e a base 3 que tem outro.')
    print()

    print('=' * 72)
    print('3. O TAMANHO DO PERIODO, PREVISTO E MEDIDO')
    print('=' * 72)
    print('   Quando a dizima existe, o periodo e a ordem multiplicativa de')
    print('   beta modulo q, retirados de q os fatores comuns com beta.')
    print()
    print('      fracao   base   previsto   medido   pre-periodo + um periodo')
    erros = 0
    for p, q, base in [(1, 10, 2), (1, 10, 4), (1, 10, 8), (1, 10, 16),
                       (1, 3, 2), (1, 5, 2), (1, 7, 10), (1, 6, 10),
                       (1, 11, 2), (1, 13, 10)]:
        f = Fraction(p, q)
        prev = periodo_previsto(f, base)
        dig, inicio, med = fracao_para_base(f, base, maximo=80)
        if prev != med:
            erros += 1
        print('      %-8s  %2d       %2d        %2d     0.%s%s'
              % ('%d/%d' % (p, q), base, prev, med, dig[:22],
                 '...' if len(dig) > 22 else ''))
    print()
    print('   %d casos, %d erro(s) de previsao.' % (10, erros))
    print()
    print('   As quatro primeiras linhas sao a mesma fracao em bases que')
    print('   sao potencias de 2, e elas contam uma historia. Em base 2 o')
    print('   periodo e 4; em base 16, que e 2^4, o periodo e 1. Um digito')
    print('   hexadecimal empacota exatamente um bloco binario de quatro')
    print('   bits, e o bloco de 1/10 e 1001, que em hexadecimal e o digito')
    print('   9. Por isso o Python imprime:')
    print('      (0.1).hex() =', (0.1).hex())
    print('   e aquela fila de noves nao e coincidencia nenhuma.')
    print()

    print('=' * 72)
    print('4. QUANTO VALE 0,1 DE VERDADE')
    print('=' * 72)
    exato = Fraction(0.1)
    print('   O que o Python guarda quando voce escreve 0.1 e esta fracao,')
    print('   e ela e exata, com numerador e denominador inteiros:')
    print()
    print('      %d / %d' % (exato.numerator, exato.denominator))
    print('      denominador = 2^%d' % round(math.log2(exato.denominator)))
    print()
    print('   Em decimal, com todos os digitos:')
    print('      0,1 guardado   = %.55f' % exato)
    print('      0,1 de verdade = 0.1000000000000000000000000000000000000000000000000000000')
    dif = exato - Fraction(1, 10)
    print('      diferenca      = %.6e' % float(dif))
    print('      erro relativo  = %.6e' % float(dif / Fraction(1, 10)))
    print('      eps/2          = %.6e' % 2.0 ** -53)
    print()
    print('   O erro relativo e menor que eps/2, que e o maximo que o')
    print('   arredondamento pode cometer. A representacao esta certa; o que')
    print('   nao existe e um 0,1 exato em binario.')
    print()
    print('   Os 64 bits, desmontados e remontados:')
    for x in (1.0, 0.1, -2.5):
        bits = format(struct.unpack('<Q', struct.pack('<d', x))[0], '064b')
        s, e, m = bits[0], bits[1:12], bits[12:]
        exp = int(e, 2) - 1023
        recon = (-1) ** int(s) * (1 + int(m, 2) / 2.0 ** 52) * 2.0 ** exp
        print('      %6r  sinal %s  expoente %5d  mantissa %16d  volta %r %s'
              % (x, s, exp, int(m, 2), recon, 'ok' if recon == x else 'FALHOU'))
    print()

    print('=' * 72)
    print('5. QUANTOS BITS POR DIGITO, E O PATRIOT')
    print('=' * 72)
    print('   Um digito decimal vale log2(10) = %.6f bits.' % math.log2(10))
    print('   Logo os 53 bits de mantissa valem %.4f digitos decimais, e os'
          % (53 * math.log10(2)))
    print('   24 bits de um float32 valem %.4f.' % (24 * math.log10(2)))
    print()
    print('   Em 25 de fevereiro de 1991, em Dhahran, uma bateria Patriot')
    print('   nao interceptou um Scud, e 28 pessoas morreram. O relatorio do')
    print('   GAO atribuiu a falha ao relogio interno, que contava decimos de')
    print('   segundo e os convertia multiplicando por uma aproximacao de 1/10')
    print('   num registrador de 24 bits.')
    print()
    print('   Refazendo a conta, para varios truncamentos:')
    print()
    print('      bits   valor guardado      erro por tique   deriva em 100 h   alvo anda')
    um_decimo = Fraction(1, 10)
    for b in range(19, 26):
        t = Fraction(int(um_decimo * 2 ** b), 2 ** b)
        e = float(um_decimo - t)
        deriva = e * 100 * 3600 * 10
        print('       %2d    %.12f      %.4e        %.4f s      %6.1f m'
              % (b, float(t), e, deriva, deriva * 1676))
    print()
    print('   A linha de 0,3433 s e a do relatorio, e ela aparece em TRES')
    print('   truncamentos diferentes, 21, 22 e 23 bits, com o mesmo valor.')
    print('   O motivo esta na expansao, nos bits 22 e 23:')
    dig = digitos_brutos(um_decimo, 2, 25)
    print('      1/10 = 0,%s...' % dig)
    print('%s%s' % (' ' * len('      1/10 = 0,') + ' ' * 21, '^^'))
    print('   os dois sao ZEROS, de modo que inclui-los nao muda o')
    print('   valor guardado. Acrescentar bits so compra precisao quando o')
    print('   bit acrescentado vale 1, e essa e a licao que o episodio deixa:')
    print('   num sistema posicional, precisao nao cresce de forma continua.')
    print()
    print('   A 1676 m/s, 0,34 s de atraso poem o alvo 575 metros adiante da')
    print('   posicao calculada, e a janela de interceptacao se fecha.')
    print()


if __name__ == '__main__':
    main()
