# -*- coding: utf-8 -*-
"""Interpolação e ajuste: Lagrange, Runge, splines e mínimos quadrados.

O QUE RESOLVE
    1. Interpola por Lagrange e mostra que o erro CRESCE com o grau na
       função de Runge, o que contraria a intuição de que mais pontos
       dão melhor resultado.
    2. Mostra que a culpa não é do polinômio e sim dos nós, trocando os
       nós igualmente espaçados pelos de Chebyshev.
    3. Compara spline cúbica com polinômio único, medindo os dois.
    4. Mede o número de condição das equações normais do ajuste
       polinomial, encontrando de novo a matriz de Hilbert da aula 1, e
       mostra o que a base ortogonal resolve.
    5. Separa interpolar de ajustar num caso com ruído, que é o caso de
       todo dado experimental.

A IDEIA
    Interpolar e ajustar sao coisas diferentes e sao confundidas o
    tempo todo. Interpolar e passar EXATAMENTE pelos pontos, e so faz
    sentido quando os pontos sao exatos: uma tabela de uma funcao
    conhecida, a saida de outro programa. Ajustar e passar PERTO deles
    segundo um criterio, e e o que se faz com medida, que tem erro.

    Usar interpolacao em dado experimental e pedir que a curva reproduza
    o ruido, e e sempre errado. Usar ajuste onde os dados sao exatos
    joga fora informacao. A primeira pergunta diante de uma tabela e
    qual dos dois casos e esse.

COMO CONFERIR SE ESTA CERTO
    1. O polinomio interpolador tem de passar pelos nos em precisao de
       maquina, qualquer que seja o grau.
    2. O erro de Runge tem de CRESCER com o grau em nos uniformes e
       CAIR em nos de Chebyshev; o programa mede os dois.
    3. A spline tem de ter segunda derivada continua nos nos internos,
       e isso e conferido numericamente.
    4. O numero de condicao das equacoes normais tem de bater com o da
       matriz de Hilbert quando os dados estao em [0,1].
    5. O ajuste por base ortogonal tem de dar o mesmo polinomio que o
       das equacoes normais quando as duas contas sao possiveis, e tem
       de continuar funcionando quando a outra ja falhou.

Prof. Apiano Morais - LFCA/URCA - Metodos Numericos
"""

import numpy as np
from scipy.interpolate import CubicSpline


# ---------------------------------------------------------------------------
# interpolação
# ---------------------------------------------------------------------------


def lagrange(xs, ys, x):
    """A fórmula de Lagrange na forma crua da definição.

    É O(n^2) por ponto avaliado e ninguém a usaria em produção, onde se
    usa a forma baricêntrica. Aqui vale pela transparência: é esta a
    fórmula que a aula deduz.
    """
    x = np.atleast_1d(np.asarray(x, float))
    s = np.zeros_like(x)
    for i in range(len(xs)):
        L = np.ones_like(x)
        for j in range(len(xs)):
            if j != i:
                L *= (x - xs[j]) / (xs[i] - xs[j])
        s += ys[i] * L
    return s


def nos_uniformes(n, a=-1.0, b=1.0):
    return np.linspace(a, b, n + 1)


def nos_chebyshev(n, a=-1.0, b=1.0):
    """Os extremos de Chebyshev, que se aglomeram nas bordas exatamente
    onde o polinômio de nós uniformes oscila."""
    k = np.arange(n + 1)
    return 0.5 * (a + b) + 0.5 * (b - a) * np.cos(np.pi * k / n)


def runge(x):
    return 1.0 / (1.0 + 25.0 * x * x)


def erro_max(f, xs, ys, n=4001, a=-1.0, b=1.0):
    t = np.linspace(a, b, n)
    return float(np.max(np.abs(lagrange(xs, ys, t) - f(t))))


# ---------------------------------------------------------------------------
# ajuste
# ---------------------------------------------------------------------------


def matriz_normal(x, grau):
    """A matriz das equações normais na base das potências, A^T A com
    A_ij = x_i^j. É simétrica e, como o programa mede, é a matriz de
    Hilbert disfarçada quando os dados estão em [0,1]."""
    m = grau + 1
    M = np.empty((m, m))
    for i in range(m):
        for j in range(m):
            M[i, j] = np.sum(x ** (i + j))
    return M


def ajuste_normal(x, y, grau):
    """Mínimos quadrados resolvendo as equações normais, que é a forma
    clássica e a que se deve evitar."""
    M = matriz_normal(x, grau)
    b = np.array([np.sum(y * x ** i) for i in range(grau + 1)])
    return np.linalg.solve(M, b)


def ajuste_qr(x, y, grau):
    """O mesmo ajuste pela decomposição QR da matriz de projeto, que é o
    que as bibliotecas sérias fazem. O número de condição que entra na
    conta é o de A, e não o de A^T A, que é o seu quadrado."""
    A = np.vander(x, grau + 1, increasing=True)
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    return coef


def main():
    print('=' * 72)
    print('1. O POLINOMIO INTERPOLADOR PASSA PELOS PONTOS')
    print('=' * 72)
    print('   Primeiro a conferencia obvia, que nao se deve pular: o')
    print('   polinomio de Lagrange de grau n passa exatamente pelos n+1')
    print('   nos, e e unico.')
    print()
    rng = np.random.default_rng(3)
    print('        n     erro maximo nos nos')
    for n in (3, 10, 20, 40, 60):
        xs = np.sort(rng.uniform(-1, 1, n + 1))
        ys = rng.uniform(-1, 1, n + 1)
        print('      %3d     %19.3e' % (n, np.max(np.abs(lagrange(xs, ys, xs) - ys))))
    print()
    print('   Zero exato, e ate grau 60 com nos sorteados ao acaso. Isso')
    print('   nao e sorte nem robustez numerica: e estrutural. Avaliando')
    print('   L_i no no x_j com j diferente de i, o fator k = j do')
    print('   produto vira (x_j - x_j), que e zero EXATO em ponto')
    print('   flutuante; e com j igual a i, todos os fatores sao')
    print('   (x_i - x_k)/(x_i - x_k), que e um exato. A soma devolve y_i')
    print('   sem nenhum arredondamento no caminho.')
    print()
    print('   Convem notar o que esse teste NAO testa, entao. Ele nao diz')
    print('   nada sobre a qualidade da interpolacao entre os nos, que e')
    print('   o assunto da secao seguinte, e nao detectaria erro nenhum')
    print('   na escolha dos nos. Um teste que passa por construcao passa')
    print('   tambem quando o programa esta errado por outro motivo.')
    print()

    print('=' * 72)
    print('2. O FENOMENO DE RUNGE: MAIS PONTOS, PIOR RESULTADO')
    print('=' * 72)
    print('   A funcao 1/(1 + 25x^2) em [-1, 1] e inocente: e suave,')
    print('   limitada, infinitamente derivavel. Interpolando-a em nos')
    print('   igualmente espacados:')
    print()
    print('        n     erro maximo       erro no centro   erro na borda')
    for n in (4, 8, 12, 16, 20, 24):
        xs = nos_uniformes(n)
        ys = runge(xs)
        t = np.linspace(-1, 1, 4001)
        d = np.abs(lagrange(xs, ys, t) - runge(t))
        # o centro TEM de ser medido fora de um no: com n par, x = 0 e
        # no, o erro ali e zero por construcao e nao mede nada
        xm = 0.5 * (xs[n // 2] + xs[n // 2 + 1])
        centro = abs(lagrange(xs, ys, np.array([xm]))[0] - runge(xm))
        borda = float(np.max(d[(t < -0.85) | (t > 0.85)]))
        print('      %3d  %15.4e  %15.2e  %14.4e'
              % (n, float(np.max(d)), centro, borda))
    print()
    print('   O erro no centro cai por um fator de quatro a cada quatro')
    print('   nos, de 3,6e-1 a 3,4e-4, e o erro na borda EXPLODE, de')
    print('   4,1e-1 a 2,6e+2. Com 24 nos o polinomio erra por centenas')
    print('   perto de +-1, numa funcao que vale no maximo 1.')
    print('   Acrescentar pontos piora, e esse e o fenomeno de Runge.')
    print()
    print('   A tentacao e culpar o polinomio. A culpa e dos NOS:')
    print()
    print('        n     uniformes        Chebyshev     razao')
    for n in (4, 8, 16, 24, 40, 60, 100):
        eu = erro_max(runge, nos_uniformes(n), runge(nos_uniformes(n)))
        ec = erro_max(runge, nos_chebyshev(n), runge(nos_chebyshev(n)))
        print('      %3d  %14.4e  %15.4e  %10.1e' % (n, eu, ec, eu / ec))
    print()
    print('   Com nos de Chebyshev o erro cai monotonicamente e chega a')
    print('   2,3e-9 em grau 100, enquanto os uniformes chegam a 1,4e+15.')
    print('   A razao entre os dois passa de 1e+23. O mesmo grau, a mesma')
    print('   funcao, o mesmo metodo: so mudaram as posicoes dos nos.')
    print()
    print('   Os nos de Chebyshev sao cos(k pi/n), que se aglomeram')
    print('   perto das bordas. Nao e coincidencia: e exatamente ali que')
    print('   o polinomio de nos uniformes oscila, e por isso e ali que')
    print('   ele precisa de mais informacao.')
    print()

    print('=' * 72)
    print('3. SPLINE CUBICA: BAIXO GRAU, MUITOS PEDACOS')
    print('=' * 72)
    print('   A outra saida e desistir de um polinomio unico. A spline')
    print('   cubica usa um polinomio de grau 3 por intervalo, colados')
    print('   com continuidade de valor, derivada primeira e segunda.')
    print()
    print('        n     Lagrange uniforme    spline cubica')
    t = np.linspace(-1, 1, 4001)
    for n in (4, 8, 12, 16, 20, 24):
        xs = nos_uniformes(n)
        ys = runge(xs)
        el_ = erro_max(runge, xs, ys)
        sp = CubicSpline(xs, ys, bc_type='natural')
        es = float(np.max(np.abs(sp(t) - runge(t))))
        print('      %3d  %19.4e  %15.4e' % (n, el_, es))
    print()
    print('   A spline nao tem o fenomeno de Runge. Com os MESMOS nos')
    print('   uniformes em que Lagrange explode, ela converge.')
    print()
    print('   Conferindo a continuidade que a spline promete, nos nos')
    print('   internos, com n = 12. A medida e por diferenca finita com')
    print('   h = 1e-7, de modo que um salto NULO aparece como 2h f\'\',')
    print('   e nao como zero:')
    xs = nos_uniformes(12)
    sp = CubicSpline(xs, runge(xs), bc_type='natural')
    h = 1e-7
    maxd = {1: 0.0, 2: 0.0, 3: 0.0}
    for xi in xs[1:-1]:
        for ordem in (1, 2, 3):
            esq = sp(xi - h, ordem)
            dir_ = sp(xi + h, ordem)
            esc = max(1.0, abs(esq), abs(dir_))
            maxd[ordem] = max(maxd[ordem], abs(esq - dir_) / esc)
    f2max = max(abs(sp(xi, 2)) for xi in xs[1:-1])
    f3max = max(abs(sp(0.5 * (xs[k] + xs[k + 1]), 3)) for k in range(12))
    for ordem in (1, 2, 3):
        print('      salto relativo maximo na derivada %d: %.3e'
              % (ordem, maxd[ordem]))
    print()
    print('      resolucao da medida, 2h vezes a derivada seguinte:')
    print('        na derivada 1:  2h |f\'\'|  ~ %.1e' % (2 * h * f2max))
    print('        na derivada 2:  2h |f\'\'\'| ~ %.1e' % (2 * h * f3max))
    print()
    print('   Os saltos nas derivadas 1 e 2 batem com a resolucao da')
    print('   medida, e portanto sao nulos ate onde da para ver: a spline')
    print('   e C2, como prometido. Ja o salto na derivada 3 vale 2,0 em')
    print('   termos relativos, e nao cai se h diminuir: ele e real. A')
    print('   terceira derivada e a primeira que a spline cubica nao')
    print('   controla, e e por ali que se percebe, olhando, que a curva')
    print('   e feita de pedacos.')
    print()
    print('   E a ordem de convergencia? Medida na propria funcao de')
    print('   Runge ela sai erratica, porque o pico em x = 0 domina o')
    print('   erro e o ponto de maximo muda de lugar conforme a malha.')
    print('   Numa funcao sem pico, sen(3x) e^(-0,3x), ela aparece:')
    print()

    def fsuave(x):
        return np.sin(3 * x) * np.exp(-0.3 * x)

    def dfsuave(x):
        return (3 * np.cos(3 * x) - 0.3 * np.sin(3 * x)) * np.exp(-0.3 * x)

    tt = np.linspace(-1, 1, 40001)
    meio = (tt > -0.8) & (tt < 0.8)
    print('        n     natural  razao   natural no meio  razao     clamped  razao')
    a = b = c = None
    for n in (8, 16, 32, 64, 128):
        xg = np.linspace(-1, 1, n + 1)
        sn = CubicSpline(xg, fsuave(xg), bc_type='natural')
        sc = CubicSpline(xg, fsuave(xg),
                         bc_type=((1, dfsuave(-1.0)), (1, dfsuave(1.0))))
        en = float(np.max(np.abs(sn(tt) - fsuave(tt))))
        em = float(np.max(np.abs(sn(tt[meio]) - fsuave(tt[meio]))))
        ec = float(np.max(np.abs(sc(tt) - fsuave(tt))))
        print('      %3d  %10.3e %6s  %14.3e %6s  %10.3e %6s'
              % (n, en, '—' if a is None else '%.1f' % (a / en),
                 em, '—' if b is None else '%.1f' % (b / em),
                 ec, '—' if c is None else '%.1f' % (c / ec)))
        a, b, c = en, em, ec
    print()
    print('   Tres colunas, tres respostas, e as tres sao informativas.')
    print()
    print('   A spline NATURAL converge com razao 4,0, isto e, em h^2. A')
    print('   mesma spline, medida so no miolo, converge muito mais')
    print('   depressa. E a spline CLAMPED, que recebe a derivada')
    print('   verdadeira nas duas pontas, converge com razao 16,0 em')
    print('   todo o intervalo, que e a ordem h^4 que a teoria preve.')
    print()
    print('   A conclusao e que a spline cubica e de quarta ordem, e que')
    print('   a condicao natural a rebaixa para segunda. O estrago fica')
    print('   confinado perto das bordas, e e por isso que a coluna do')
    print('   meio escapa dele ate que o erro de borda alcance o de')
    print('   dentro, o que acontece em n = 128.')
    print()
    print('   Convem dizer que essa medida nao sai da funcao de Runge. O')
    print('   pico dela em x = 0 tem quarta derivada enorme e domina o')
    print('   erro, mascarando o efeito de borda; so trocando para uma')
    print('   funcao sem pico e que as tres colunas se separam. Escolher')
    print('   o caso de teste faz parte de medir.')
    print()
    print('   O preco da spline natural aparece tambem na ponta:')
    print('      f\'\'(-1) verdadeira: %+.4f' % (
        (runge(-1 + 1e-5) - 2 * runge(-1.0) + runge(-1 - 1e-5)) / 1e-10))
    print('      f\'\'(-1) da spline:  %+.4f' % sp(-1.0, 2))
    print('   Zero, porque foi imposto. Quando se conhece a derivada nas')
    print('   bordas, a spline completa usa essa informacao, e a tabela')
    print('   acima mostra o que se ganha com isso.')
    print()

    print('=' * 72)
    print('4. AJUSTE: AS EQUACOES NORMAIS SAO HILBERT DISFARCADA')
    print('=' * 72)
    print('   Ajustar um polinomio de grau g a m pontos, por minimos')
    print('   quadrados na base das potencias, leva a resolver A^T A c =')
    print('   A^T y. Medindo o numero de condicao dessa matriz:')
    print()
    x = np.linspace(0, 1, 200)
    print('        grau    cond(A^T A)     cond(A)     razao   cond(Hilbert)')
    for g in (3, 5, 7, 9, 11):
        M = matriz_normal(x, g)
        A = np.vander(x, g + 1, increasing=True)
        i = np.arange(1, g + 2)
        H = 1.0 / (i[:, None] + i[None, :] - 1)
        cM, cA, cH = (np.linalg.cond(M), np.linalg.cond(A), np.linalg.cond(H))
        print('      %5d  %13.3e  %10.3e  %8.1f  %13.3e'
              % (g, cM, cA, cM / cA ** 2, cH))
    print()
    print('   Duas coisas saltam. A primeira: cond(A^T A) e exatamente o')
    print('   QUADRADO de cond(A), e a coluna da razao mostra isso. Quem')
    print('   monta as equacoes normais esta elevando ao quadrado o')
    print('   condicionamento do problema, e portanto jogando fora METADE')
    print('   dos digitos antes de comecar a resolver.')
    print()
    print('   A segunda: a ordem de grandeza bate com a da matriz de')
    print('   Hilbert do mesmo tamanho, que foi o exemplo de problema mal')
    print('   condicionado da aula 1. Nao e analogia: com os dados em')
    print('   [0,1], a soma de x^(i+j) dividida por m e uma aproximacao')
    print('   da integral de x^(i+j), que vale 1/(i+j+1). As equacoes')
    print('   normais na base das potencias SAO Hilbert.')
    print()
    print('   O efeito pratico, ajustando um polinomio a dados gerados')
    print('   por um polinomio conhecido, sem ruido nenhum:')
    print()
    coef_ex = np.array([1.0, -2.0, 3.0, -1.5, 0.7, 2.2, -1.1, 0.4,
                        -0.9, 1.3, 0.6, -0.3])
    print('        grau   erro max nos coeficientes')
    print('                normais        QR')
    for g in (3, 5, 7, 9, 11):
        y = np.polyval(coef_ex[:g + 1][::-1], x)
        cn = ajuste_normal(x, y, g)
        cq = ajuste_qr(x, y, g)
        en = np.max(np.abs(cn - coef_ex[:g + 1]))
        eq = np.max(np.abs(cq - coef_ex[:g + 1]))
        print('      %5d  %13.3e  %11.3e' % (g, en, eq))
    print()
    print('   Em grau 11 as equacoes normais erram o coeficiente em 0,65,')
    print('   num polinomio cujos coeficientes sao da ordem de 1: nao')
    print('   sobrou digito nenhum. O QR erra 1,8e-9, e ainda tem nove.')
    print('   A diferenca nao esta na matematica, que e a mesma, e sim em')
    print('   nunca formar A^T A: o QR trabalha com A, cujo numero de')
    print('   condicao e a raiz quadrada do de A^T A.')
    print()

    print('=' * 72)
    print('5. INTERPOLAR OU AJUSTAR: A PERGUNTA QUE VEM ANTES')
    print('=' * 72)
    print('   Dados experimentais de um decaimento exponencial, com 2 por')
    print('   cento de ruido relativo, 15 pontos:')
    print()
    rng = np.random.default_rng(11)
    xd = np.linspace(0, 3, 15)
    verdade = 5.0 * np.exp(-1.3 * xd)
    yd = verdade * (1 + 0.02 * rng.standard_normal(len(xd)))
    tt = np.linspace(0, 3, 2001)
    vv = 5.0 * np.exp(-1.3 * tt)

    pol = lagrange(xd, yd, tt)
    sp = CubicSpline(xd, yd)
    cq = ajuste_qr(xd, np.log(yd), 1)
    exp_aj = np.exp(cq[0]) * np.exp(cq[1] * tt)

    print('      metodo                 erro max contra a verdade   passa nos pontos')
    print('      Lagrange grau 14  %22.3e   sim' % np.max(np.abs(pol - vv)))
    print('      spline cubica     %22.3e   sim' % np.max(np.abs(sp(tt) - vv)))
    print('      ajuste exponencial%22.3e   nao' % np.max(np.abs(exp_aj - vv)))
    print()
    print('   Os dois primeiros passam exatamente pelos 15 pontos e os')
    print('   dois erram mais que o terceiro, que nao passa por nenhum.')
    print('   A razao e que os pontos estao errados: eles tem 2 por cento')
    print('   de ruido, e exigir que a curva passe por eles e exigir que')
    print('   ela reproduza o ruido.')
    print()
    print('   Os parametros recuperados pelo ajuste:')
    print('      A  = %.4f   (verdadeiro 5,0000)' % np.exp(cq[0]))
    print('      k  = %.4f   (verdadeiro 1,3000)' % (-cq[1]))
    print()
    print('   Com 15 pontos e 2 por cento de ruido, o ajuste de dois')
    print('   parametros recupera a constante de decaimento com erro de')
    print('   %.1f por cento. Nenhuma interpolacao faria isso, porque'
          % abs(100 * (-cq[1] / 1.3 - 1)))
    print('   interpolacao nao tem como saber que o ruido e ruido.')
    print()
    print('   A regra, entao: pontos exatos pedem interpolacao, e pontos')
    print('   medidos pedem ajuste. E a escolha entre um polinomio de')
    print('   grau alto e uma spline e outra conversa, que so aparece')
    print('   depois de resolvida esta.')
    print()


if __name__ == '__main__':
    main()
