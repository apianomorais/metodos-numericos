# -*- coding: utf-8 -*-
"""Integração numérica: trapézios, Simpson, Romberg e quadratura gaussiana.

O QUE RESOLVE
    1. Mede a ordem de convergência de trapézios e de Simpson, e
       confere contra h^2 e h^4.
    2. Mostra que Simpson sai de graça da extrapolação de Richardson
       aplicada aos trapézios, e constrói Romberg a partir dali.
    3. Compara quadratura gaussiana com as regras de Newton-Cotes a
       igual número de avaliações da função, que é a comparação justa.
    4. Exibe os dois casos em que tudo isso falha: integrando com
       derivada infinita na borda e integrando um periódico, onde o
       trapézio humilha Simpson.
    5. Mede o piso de arredondamento, abaixo do qual refinar a malha
       PIORA o resultado.

A IDEIA
    Toda regra de Newton-Cotes e a mesma receita: trocar a funcao por
    um polinomio interpolador e integrar o polinomio, que se integra
    exatamente. Trapezio usa reta, Simpson usa parabola, e dai em
    diante o grau sobe. A ordem do erro sai de Taylor, e sai com uma
    surpresa: Simpson, que usa parabola, acerta tambem as cubicas, e
    por isso e de quarta ordem e nao de terceira.

    A quadratura gaussiana faz a pergunta que Newton-Cotes nao faz.
    Fixado o numero n de avaliacoes, Newton-Cotes escolhe os pontos
    igualmente espacados e ajusta so os pesos, o que da n parametros e
    exatidao ate grau n-1. Gauss ajusta tambem as POSICOES, o que da 2n
    parametros e exatidao ate grau 2n-1. E a mesma ideia dos nos de
    Chebyshev da aula 3: escolher onde medir vale tanto quanto escolher
    como combinar.

COMO CONFERIR SE ESTA CERTO
    1. As ordens medidas tem de dar 2 para trapezio e 4 para Simpson,
       pela razao de erros ao dobrar n.
    2. A segunda coluna de Romberg tem de ser IGUAL a Simpson, em
       precisao de maquina, porque ela e Simpson.
    3. Gauss com n nos tem de integrar exatamente todo polinomio de
       grau ate 2n-1, e errar no grau 2n.
    4. Nos casos patologicos, a ordem medida tem de cair, e o programa
       diz para quanto.
    5. O piso de arredondamento tem de aparecer perto de n = 1/raiz(eps)
       para o trapezio, e o programa mede onde ele aparece.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import numpy as np
from scipy.integrate import quad


# ---------------------------------------------------------------------------
# as regras, escritas na forma mais transparente
# ---------------------------------------------------------------------------


def trapezios(f, a, b, n):
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h * (0.5 * y[0] + y[1:-1].sum() + 0.5 * y[-1])


def simpson(f, a, b, n):
    """n tem de ser par: a regra usa pares de intervalos."""
    if n % 2:
        n += 1
    x = np.linspace(a, b, n + 1)
    y = f(x)
    h = (b - a) / n
    return h / 3 * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())


def romberg(f, a, b, niveis):
    """A tabela de Romberg: primeira coluna de trapézios, e cada coluna
    seguinte extrapolada da anterior por Richardson."""
    T = np.zeros((niveis, niveis))
    for i in range(niveis):
        T[i, 0] = trapezios(f, a, b, 2 ** i)
        for j in range(1, i + 1):
            q = 4 ** j
            T[i, j] = (q * T[i, j - 1] - T[i - 1, j - 1]) / (q - 1)
    return T


def gauss_legendre(n):
    """Nós e pesos de Gauss-Legendre em [-1,1], pelas raízes de P_n
    achadas por Newton, com a recorrência de três termos."""
    no = np.zeros(n)
    peso = np.zeros(n)
    for i in range(n):
        x = np.cos(np.pi * (i + 0.75) / (n + 0.5))
        for _ in range(100):
            p0, p1 = 1.0, 0.0
            for k in range(n):
                p0, p1 = ((2 * k + 1) * x * p0 - k * p1) / (k + 1), p0
            dp = n * (x * p0 - p1) / (x * x - 1)
            dx = -p0 / dp
            x += dx
            if abs(dx) < 1e-15:
                break
        no[i] = x
        peso[i] = 2 / ((1 - x * x) * dp * dp)
    return no, peso


def quad_gauss(f, a, b, n):
    no, peso = gauss_legendre(n)
    c, d = 0.5 * (b - a), 0.5 * (b + a)
    return c * np.sum(peso * f(c * no + d))


def ordem(err_n, err_2n):
    """A ordem p sai de err(h)/err(h/2) = 2^p."""
    if err_2n <= 0 or err_n <= 0:
        return float('nan')
    return np.log2(err_n / err_2n)


def main():
    print('=' * 72)
    print('1. AS ORDENS DE TRAPEZIO E SIMPSON, MEDIDAS')
    print('=' * 72)
    f = np.sin
    exato = 2.0                      # integral de sen de 0 a pi
    print('   Integral de sen(x) de 0 a pi, que vale exatamente 2.')
    print()
    print('        n     trapezio      erro      ordem      Simpson      erro      ordem')
    et_ant = es_ant = None
    for n in (4, 8, 16, 32, 64, 128):
        t = trapezios(f, 0, np.pi, n)
        sm = simpson(f, 0, np.pi, n)
        et, es = abs(t - exato), abs(sm - exato)
        print('      %4d  %11.8f  %.2e  %7s  %11.8f  %.2e  %7s'
              % (n, t, et, '—' if et_ant is None else '%.3f' % ordem(et_ant, et),
                 sm, es, '—' if es_ant is None else '%.3f' % ordem(es_ant, es)))
        et_ant, es_ant = et, es
    print()
    print('   As duas colunas de ordem dao 2,000 e 4,000, que e o que a')
    print('   expansao de Taylor preve. Em n = 128 o trapezio tem 5')
    print('   digitos corretos e o Simpson tem 11, com o MESMO numero de')
    print('   avaliacoes da funcao.')
    print()
    print('   A surpresa de Simpson vale ser conferida: a regra usa uma')
    print('   parabola por par de intervalos, e deveria portanto ser')
    print('   exata ate grau 2. Ela e exata ate grau 3:')
    print()
    print('        grau   integral de x^k em [0,1]   Simpson com n=2    erro')
    for k in range(6):
        ex = 1.0 / (k + 1)
        ap = simpson(lambda x, k=k: x ** k, 0, 1, 2)
        print('        %2d   %22.15f  %17.15f  %.1e'
              % (k, ex, ap, abs(ap - ex)))
    print()
    print('   O grau 3 passa de graca, e e por isso que Simpson e de')
    print('   quarta ordem. A razao e a simetria: o erro da parabola')
    print('   sobre a cubica e impar em torno do ponto medio do par de')
    print('   intervalos, e se cancela entre as duas metades.')
    print()

    print('=' * 72)
    print('2. SIMPSON SAI DE GRACA, POR RICHARDSON')
    print('=' * 72)
    print('   Se o erro do trapezio e C h^2 + O(h^4), entao combinando')
    print('   T(h) e T(h/2) da para matar o termo em h^2:')
    print()
    print('      T(h)   = I + C h^2')
    print('      T(h/2) = I + C h^2/4')
    print('      logo   I = [4 T(h/2) - T(h)]/3,  a menos de O(h^4)')
    print()
    print('   Essa combinacao TEM de dar Simpson, e a conferencia e')
    print('   direta:')
    print()
    print('        n      [4T(n) - T(n/2)]/3        Simpson(n)        diferenca')
    for n in (4, 8, 16, 32, 64):
        rich = (4 * trapezios(f, 0, np.pi, n) - trapezios(f, 0, np.pi, n // 2)) / 3
        sm = simpson(f, 0, np.pi, n)
        print('      %4d  %22.16f  %18.16f  %.1e'
              % (n, rich, sm, abs(rich - sm)))
    print()
    print('   Iguais em precisao de maquina. Simpson nao precisava ter')
    print('   sido inventado separadamente: ele e o trapezio extrapolado.')
    print()
    print('   E nada impede repetir. Matando o h^4 chega-se a ordem 6, e')
    print('   assim por diante: isso e a tabela de Romberg.')
    print()
    T = romberg(f, 0, np.pi, 7)
    print('        n          trapezio        ordem 4          ordem 6          ordem 8')
    for i in range(7):
        linha = '      %4d' % 2 ** i
        for j in range(min(i + 1, 4)):
            linha += '  %16.12f' % T[i, j]
        print(linha)
    print()
    print('      melhor valor de Romberg: %.16f' % T[6, 6])
    print('      exato:                   %.16f' % exato)
    print('      erro: %.2e, com apenas %d avaliacoes'
          % (abs(T[6, 6] - exato), 2 ** 6 + 1))
    print()
    print('   Com 65 avaliacoes Romberg chega a precisao de maquina,')
    print('   enquanto o trapezio sozinho, com as mesmas 65, tem 4')
    print('   digitos. A extrapolacao nao custou avaliacao nenhuma: ela')
    print('   e aritmetica sobre resultados que ja se tinha.')
    print()

    print('=' * 72)
    print('3. QUADRATURA GAUSSIANA: ESCOLHER ONDE MEDIR')
    print('=' * 72)
    print('   Newton-Cotes fixa os pontos igualmente espacados e ajusta')
    print('   os pesos: sao n parametros, e exatidao ate grau n-1. Gauss')
    print('   ajusta tambem as posicoes: 2n parametros, e exatidao ate')
    print('   grau 2n-1. Conferindo essa promessa com n = 3:')
    print()
    print('        grau k   integral de x^k em [-1,1]   Gauss n=3      erro')
    for k in range(8):
        ex = 0.0 if k % 2 else 2.0 / (k + 1)
        ap = quad_gauss(lambda x, k=k: x ** k, -1, 1, 3)
        marca = '  <- primeiro erro' if abs(ap - ex) > 1e-12 else ''
        print('        %3d   %24.15f  %13.9f  %.1e%s'
              % (k, ex, ap, abs(ap - ex), marca))
    print()
    print('   Exato ate grau 5 e errado em grau 6, que e exatamente')
    print('   2n-1 = 5. A promessa se cumpre no limite.')
    print()
    print('   E a comparacao que importa, a igual numero de avaliacoes:')
    print()
    print('   O numero de avaliacoes e impar para que Simpson caiba')
    print('   exatamente: com k avaliacoes ele usa k-1 intervalos, e')
    print('   esse numero tem de ser par.')
    print()
    print('        aval.    trapezio      Simpson        Gauss')
    for k in (3, 5, 7, 9, 11, 13):
        et = abs(trapezios(f, 0, np.pi, k - 1) - exato)
        es = abs(simpson(f, 0, np.pi, k - 1) - exato)
        eg = abs(quad_gauss(f, 0, np.pi, k) - exato)
        print('      %5d  %12.3e  %11.3e  %12.3e' % (k, et, es, eg))
    print()
    print('   Com 9 avaliacoes Gauss ja esta em 1e-15 e o Simpson em')
    print('   1e-4; com 13, Gauss esta no limite da maquina e o Simpson')
    print('   ainda nao chegou a 1e-5. A diferenca nao e de constante, e')
    print('   de ORDEM: para funcoes analiticas Gauss converge')
    print('   exponencialmente com o numero de nos, e Newton-Cotes')
    print('   converge como potencia de h.')
    print()

    print('=' * 72)
    print('4. ONDE TUDO ISSO FALHA')
    print('=' * 72)
    print('   (a) Derivada infinita na borda: integral de raiz(x) em')
    print('       [0,1], que vale 2/3.')
    print()
    exato_r = 2.0 / 3.0
    fr = np.sqrt
    print('          n     erro trapezio   ordem    erro Simpson   ordem')
    et_ant = es_ant = None
    for n in (16, 32, 64, 128, 256, 512):
        et = abs(trapezios(fr, 0, 1, n) - exato_r)
        es = abs(simpson(fr, 0, 1, n) - exato_r)
        print('       %5d  %14.3e  %6s  %14.3e  %6s'
              % (n, et, '—' if et_ant is None else '%.3f' % ordem(et_ant, et),
                 es, '—' if es_ant is None else '%.3f' % ordem(es_ant, es)))
        et_ant, es_ant = et, es
    print()
    print('       As ordens caem de 2 e 4 para 1,5, as duas. A culpa e')
    print('       da derivada de raiz(x), que e infinita em x = 0: a')
    print('       deducao por Taylor supos derivadas limitadas, e aqui')
    print('       elas nao sao. Nenhuma regra de Newton-Cotes escapa, e')
    print('       aumentar a ordem da regra nao adianta nada.')
    print()
    print('       A saida e mudar a variavel. Com x = u^2, dx = 2u du:')
    print('       a integral vira a de 2u^2 em [0,1], que e polinomial.')
    g = lambda u: 2 * u * u
    print('          n = 4, Simpson na forma trocada: %.16f' % simpson(g, 0, 1, 4))
    print('          exato:                           %.16f' % exato_r)
    print('          erro: %.1e' % abs(simpson(g, 0, 1, 4) - exato_r))
    print()
    print('       Quatro intervalos e precisao de maquina, contra 512 e')
    print('       cinco digitos na forma original. A mudanca de variavel')
    print('       vale mais que qualquer refinamento de malha.')
    print()
    print('   (b) O caso oposto: funcao periodica no periodo inteiro.')
    print()
    print('       Integral de 1/(2 + cos x) de 0 a 2pi, que vale')
    print('       2pi/raiz(3).')
    print()
    fp = lambda x: 1.0 / (2.0 + np.cos(x))
    exato_p = 2 * np.pi / np.sqrt(3)
    print('          n     erro trapezio    erro Simpson')
    for n in (4, 8, 12, 16, 20, 24):
        print('       %5d  %14.3e  %14.3e'
              % (n, abs(trapezios(fp, 0, 2 * np.pi, n) - exato_p),
                 abs(simpson(fp, 0, 2 * np.pi, n) - exato_p)))
    print()
    print('       Aqui o TRAPEZIO humilha o Simpson. Com 24 pontos ele')
    print('       chega a 1,4e-13, e o Simpson ainda esta em 3,3e-7, seis')
    print('       ordens de grandeza atras. A razao e que, num periodo')
    print('       completo de uma funcao suave e periodica,')
    print('       os termos de erro do trapezio se cancelam todos')
    print('       pela formula de Euler-Maclaurin, e a convergencia vira')
    print('       exponencial. Simpson, ao ponderar os pontos de forma')
    print('       alternada 4-2-4-2, QUEBRA essa simetria e estraga o')
    print('       cancelamento.')
    print()
    print('       E a licao geral desta secao: nao existe regra melhor,')
    print('       existe regra adequada ao integrando. Quem usa Simpson')
    print('       em tudo esta errando nos dois casos acima.')
    print()

    print('=' * 72)
    print('5. O PISO DE ARREDONDAMENTO')
    print('=' * 72)
    print('   Refinar a malha reduz o erro de truncamento e aumenta o de')
    print('   arredondamento, porque sao mais parcelas somadas. Em algum')
    print('   n os dois se cruzam, e dali em diante refinar PIORA. Essa e')
    print('   a previsao; convem testa-la.')
    print()

    def trap_seq(n):
        """O mesmo trapezio, somando sequencialmente. O np.cumsum acumula
        da esquerda para a direita, que e o que faz um laco escrito a
        mao; o np.sum, nao."""
        x = np.linspace(0, np.pi, n + 1)
        y = np.sin(x)
        h = np.pi / n
        return h * (0.5 * y[0] + np.cumsum(y[1:-1])[-1] + 0.5 * y[-1])

    print('        n        com np.sum      com soma sequencial')
    melhor_np = (np.inf, 0)
    melhor_sq = (np.inf, 0)
    for p in (10, 14, 18, 20, 21, 22, 23, 24):
        n = 2 ** p
        enp = abs(trapezios(f, 0, np.pi, n) - exato)
        esq = abs(trap_seq(n) - exato)
        melhor_np = min(melhor_np, (enp, n))
        melhor_sq = min(melhor_sq, (esq, n))
        print('      %10d  %14.3e  %20.3e' % (n, enp, esq))
    print()
    print('   As duas colunas se separam no fim, e so uma delas se')
    print('   comporta como a previsao dizia.')
    print()
    print('      soma sequencial: melhor em n = %d, erro %.3e'
          % (melhor_sq[1], melhor_sq[0]))
    print('      depois disso ela PIORA, de %.3e para %.3e'
          % (melhor_sq[0], abs(trap_seq(2 ** 24) - exato)))
    print()
    print('      com np.sum: melhor em n = %d, erro %.3e'
          % (melhor_np[1], melhor_np[0]))
    print('      e ainda estava melhorando quando a varredura acabou')
    print()
    eps = np.finfo(float).eps
    otimo = (2.58 / (2 * eps)) ** 0.4
    print('   O modelo ingenuo preve o piso da coluna sequencial. O erro')
    print('   de truncamento do trapezio em sen sobre [0,pi] vale')
    print('   pi^3/(12 n^2) = 2,58/n^2, e o de arredondamento de uma soma')
    print('   sequencial de n parcelas cresce como raiz(n) eps. Igualando')
    print('   os dois:')
    print()
    print('      n otimo previsto: %.2e' % otimo)
    print('      n otimo medido:   %.2e' % melhor_sq[1])
    print('      razao: %.1f' % (melhor_sq[1] / otimo))
    print()
    print('   Mesma ordem de grandeza, que e o que um modelo desses pode')
    print('   dar: ele supoe que os erros de arredondamento sao')
    print('   independentes e se somam como passeio aleatorio, e eles nao')
    print('   sao exatamente independentes.')
    print()
    print('   Ja a coluna do np.sum nao tem piso a vista, e a razao e a')
    print('   mesma da aula 1: o np.sum soma por PARES, e o erro dessa')
    print('   soma cresce como raiz(log n) em vez de raiz(n). Com n =')
    print('   1,7e7, raiz(n) vale 4100 e raiz(log n) vale 4,9: o piso fica')
    print('   quase mil vezes mais baixo, e a varredura nao chega nele.')
    print()
    print('   Duas conclusoes praticas, e a segunda e a que importa.')
    print()
    print('   A primeira e que o piso existe e depende de COMO se soma,')
    print('   e nao so de quantas parcelas. Quem escreve o laco a mao')
    print('   encontra o piso cedo; quem usa np.sum, muito mais tarde.')
    print()
    print('   A segunda e que nada disso deveria importar, porque chegar')
    print('   perto do piso ja e sintoma de ter escolhido mal o metodo.')
    print('   Para obter 1e-13 o trapezio precisou de milhoes de pontos,')
    print('   e Romberg conseguiu 4e-16 com 65. A saida para o piso de')
    print('   arredondamento nao e somar melhor: e subir a ordem do')
    print('   metodo e nunca precisar de malha tao fina.')
    print()
    print('   Conferindo tudo contra a biblioteca, para fechar:')
    v, err = quad(fp, 0, 2 * np.pi)
    print('      scipy.quad em 1/(2+cos x): %.16f' % v)
    print('      exato:                     %.16f' % exato_p)
    print('      erro estimado pela quad:   %.1e' % err)
    print('      erro verdadeiro:           %.1e' % abs(v - exato_p))
    print()


if __name__ == '__main__':
    main()
