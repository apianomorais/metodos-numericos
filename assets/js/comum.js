/* ===================================================================
   comum.js — configuração do MathJax, navegação e utilitários gráficos
   Fenômenos de Transporte / LFCA / URCA
   =================================================================== */

/* ---------- MathJax ---------- */
window.MathJax = {
  tex: {
    inlineMath: [['\\(', '\\)'], ['$', '$']],
    displayMath: [['\\[', '\\]'], ['$$', '$$']],
    processEscapes: true,
    macros: {
      med: ['\\langle #1 \\rangle', 1],
      /* notação brasileira: sen, tg, cotg, arcsen.
         Redefinimos \sin e \tan para que qualquer fórmula escrita no padrão
         internacional também apareça na notação usada em sala. */
      sen: '\\operatorname{sen}',
      sin: '\\operatorname{sen}',
      tg: '\\operatorname{tg}',
      tan: '\\operatorname{tg}',
      cotg: '\\operatorname{cotg}',
      cot: '\\operatorname{cotg}',
      arcsen: '\\operatorname{arcsen}',
      arcsin: '\\operatorname{arcsen}',
      arctg: '\\operatorname{arctg}',
      arctan: '\\operatorname{arctg}',
      senh: '\\operatorname{senh}',
      sinh: '\\operatorname{senh}',
      tgh: '\\operatorname{tgh}',
      tanh: '\\operatorname{tgh}',
      /* mecânica clássica: vetores com seta, versores com chapéu,
         tensores em sem-serifa. A hamiltoniana fica com o H reto e a
         lagrangiana com o L caligráfico, como em Goldstein. */
      vet: ['\\vec{#1}', 1],
      vers: ['\\hat{#1}', 1],
      Ten: ['\\mathsf{#1}', 1],
      Lag: '\\mathcal{L}',
      Acao: '\\mathcal{S}',
      der: ['\\frac{d #1}{d #2}', 2],
      dder: ['\\frac{d^2 #1}{d #2^2}', 2],
      pder: ['\\frac{\\partial #1}{\\partial #2}', 2],
      dpar: ['\\left(\\frac{\\partial #1}{\\partial #2}\\right)_{#3}', 3],
      med: ['\\left\\langle #1 \\right\\rangle', 1],
      kB: 'k_B',
      Tr: '\\operatorname{Tr}',
      cruz: '\\times',
      R: '\\mathbb{R}',
      N: '\\mathbb{N}'
    }
  },
  options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'] },
  svg: { fontCache: 'global' }
};

/* ---------- Índice lateral ativo durante a rolagem ---------- */
document.addEventListener('DOMContentLoaded', function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('.lateral a[href^="#"]'));
  if (!links.length) return;
  var alvos = links.map(function (a) {
    return document.getElementById(a.getAttribute('href').slice(1));
  }).filter(Boolean);

  function atualizar() {
    var y = window.scrollY + 110, atual = null;
    alvos.forEach(function (el) { if (el.offsetTop <= y) atual = el; });
    links.forEach(function (a) {
      a.classList.toggle('ativo', atual && a.getAttribute('href') === '#' + atual.id);
    });
  }
  var pendente = false;
  window.addEventListener('scroll', function () {
    if (pendente) return;
    pendente = true;
    window.requestAnimationFrame(function () { atualizar(); pendente = false; });
  }, { passive: true });
  atualizar();
});
/* ===================================================================
   N — utilitários de cálculo numérico
   Tudo aqui é escrito na forma mais transparente possível, e não na
   mais rápida: estes são os métodos que as aulas estudam, e o aluno
   precisa poder ler o código e reconhecer a fórmula.
   =================================================================== */
var N = (function () {

  /* ---------- o que a máquina pode e não pode ---------- */

  /* O épsilon da máquina, medido em vez de citado: o menor e tal que
     1 + e ainda difere de 1. Em float64 dá 2,220446049250313e-16. */
  function epsilonMaquina() {
    var e = 1.0;
    while (1.0 + e / 2.0 !== 1.0) e = e / 2.0;
    return e;
  }

  /* O próximo float depois de x, na direção de y. É o nextafter do C, e
     serve para medir a granularidade local da reta de ponto flutuante. */
  var _buf = new DataView(new ArrayBuffer(8));
  function proximoFloat(x, y) {
    if (isNaN(x) || isNaN(y)) return NaN;
    if (x === y) return x;
    if (x === 0) return y > 0 ? Number.MIN_VALUE : -Number.MIN_VALUE;
    _buf.setFloat64(0, x);
    var hi = _buf.getUint32(0), lo = _buf.getUint32(4);
    var subir = (y > x) === (x > 0);
    if (subir) {
      lo = (lo + 1) >>> 0;
      if (lo === 0) hi = (hi + 1) >>> 0;
    } else {
      if (lo === 0) hi = (hi - 1) >>> 0;
      lo = (lo - 1) >>> 0;
    }
    _buf.setUint32(0, hi); _buf.setUint32(4, lo);
    return _buf.getFloat64(0);
  }

  /* Quantos floats cabem entre a e b. É a medida honesta de erro quando
     os números são grandes: dizer "errou dois ulps" diz mais do que
     dizer "errou 1e-9". */
  function ulps(a, b) {
    if (a === b) return 0;
    var n = 0, x = Math.min(a, b), alvo = Math.max(a, b);
    while (x < alvo && n < 1e7) { x = proximoFloat(x, alvo); n++; }
    return n;
  }

  /* Soma compensada de Kahan: carrega o erro de arredondamento de uma
     parcela para a seguinte, e com isso a soma de n termos erra como se
     fossem poucos, em vez de crescer com n. */
  function somaKahan(v) {
    var s = 0, c = 0;
    for (var i = 0; i < v.length; i++) {
      var y = v[i] - c, t = s + y;
      c = (t - s) - y;
      s = t;
    }
    return s;
  }

  function somaIngenua(v) {
    var s = 0;
    for (var i = 0; i < v.length; i++) s += v[i];
    return s;
  }

  /* ---------- raízes ---------- */

  /* Bisseção. Devolve a raiz e o histórico dos intervalos, porque o que
     interessa pedagogicamente é ver o intervalo encolher pela metade. */
  function bissecao(f, a, b, tol, maxit) {
    tol = tol || 1e-12; maxit = maxit || 200;
    var fa = f(a), fb = f(b), passos = [];
    if (fa * fb > 0) return { raiz: NaN, passos: passos, erro: 'sem troca de sinal' };
    for (var k = 0; k < maxit && (b - a) / 2 > tol; k++) {
      var m = (a + b) / 2, fm = f(m);
      passos.push({ a: a, b: b, m: m, fm: fm });
      if (fa * fm <= 0) { b = m; fb = fm; } else { a = m; fa = fm; }
    }
    return { raiz: (a + b) / 2, passos: passos };
  }

  /* Newton-Raphson. Guarda o histórico para que a ordem de convergência
     possa ser MEDIDA, e não apenas afirmada. */
  function newton(f, fl, x0, tol, maxit) {
    tol = tol || 1e-14; maxit = maxit || 100;
    var x = x0, passos = [{ x: x, fx: f(x) }];
    for (var k = 0; k < maxit; k++) {
      var d = fl(x);
      if (d === 0) return { raiz: NaN, passos: passos, erro: 'derivada nula' };
      var novo = x - f(x) / d;
      passos.push({ x: novo, fx: f(novo) });
      if (Math.abs(novo - x) < tol) return { raiz: novo, passos: passos };
      x = novo;
    }
    return { raiz: x, passos: passos, erro: 'não convergiu' };
  }

  function secante(f, x0, x1, tol, maxit) {
    tol = tol || 1e-14; maxit = maxit || 100;
    var f0 = f(x0), f1 = f(x1), passos = [{ x: x0, fx: f0 }, { x: x1, fx: f1 }];
    for (var k = 0; k < maxit; k++) {
      if (f1 === f0) return { raiz: NaN, passos: passos, erro: 'secante horizontal' };
      var x2 = x1 - f1 * (x1 - x0) / (f1 - f0);
      passos.push({ x: x2, fx: f(x2) });
      if (Math.abs(x2 - x1) < tol) return { raiz: x2, passos: passos };
      x0 = x1; f0 = f1; x1 = x2; f1 = f(x2);
    }
    return { raiz: x1, passos: passos, erro: 'não convergiu' };
  }

  /* A ordem de convergência medida dos próprios passos, pela razão de
     logaritmos de erros sucessivos. Sem raiz exata não há como medir, e
     por isso ela entra como argumento. */
  function ordemMedida(passos, raiz) {
    var e = passos.map(function (p) { return Math.abs(p.x - raiz); })
                  .filter(function (v) { return v > 0; });
    var ord = [];
    for (var i = 2; i < e.length; i++) {
      var d = Math.log(e[i - 1] / e[i - 2]);
      if (Math.abs(d) > 1e-12) ord.push(Math.log(e[i] / e[i - 1]) / d);
    }
    return ord;
  }

  /* ---------- interpolação ---------- */

  /* Lagrange na forma crua da definição. É O(n^2) por ponto e ninguém
     usaria assim em produção, mas é esta a fórmula que a aula deduz. */
  function lagrange(xs, ys, x) {
    var s = 0;
    for (var i = 0; i < xs.length; i++) {
      var L = 1;
      for (var j = 0; j < xs.length; j++) {
        if (j !== i) L *= (x - xs[j]) / (xs[i] - xs[j]);
      }
      s += ys[i] * L;
    }
    return s;
  }

  /* Spline cúbica natural: segunda derivada nula nas pontas. Resolve o
     sistema tridiagonal pelo algoritmo de Thomas. */
  function splineNatural(xs, ys) {
    var n = xs.length - 1;
    var h = [], i;
    for (i = 0; i < n; i++) h.push(xs[i + 1] - xs[i]);
    var al = new Array(n).fill(0);
    for (i = 1; i < n; i++) {
      al[i] = 3 * (ys[i + 1] - ys[i]) / h[i] - 3 * (ys[i] - ys[i - 1]) / h[i - 1];
    }
    var l = [1], mu = [0], z = [0], c = new Array(n + 1).fill(0),
        b = new Array(n).fill(0), d = new Array(n).fill(0);
    for (i = 1; i < n; i++) {
      l.push(2 * (xs[i + 1] - xs[i - 1]) - h[i - 1] * mu[i - 1]);
      mu.push(h[i] / l[i]);
      z.push((al[i] - h[i - 1] * z[i - 1]) / l[i]);
    }
    l.push(1); z.push(0);
    for (i = n - 1; i >= 0; i--) {
      c[i] = z[i] - mu[i] * c[i + 1];
      b[i] = (ys[i + 1] - ys[i]) / h[i] - h[i] * (c[i + 1] + 2 * c[i]) / 3;
      d[i] = (c[i + 1] - c[i]) / (3 * h[i]);
    }
    return function (x) {
      var k = 0;
      while (k < n - 1 && x > xs[k + 1]) k++;
      var t = x - xs[k];
      return ys[k] + b[k] * t + c[k] * t * t + d[k] * t * t * t;
    };
  }

  /* Mínimos quadrados polinomial pelas equações normais. Elas são a
     forma clássica e são também MAL CONDICIONADAS: é de propósito, e a
     aula de condicionamento volta a este ponto. */
  function minimosQuadrados(xs, ys, grau) {
    var m = grau + 1, A = [], i, j, k;
    for (i = 0; i < m; i++) {
      A.push([]);
      for (j = 0; j < m; j++) {
        var s = 0;
        for (k = 0; k < xs.length; k++) s += Math.pow(xs[k], i + j);
        A[i].push(s);
      }
      var t = 0;
      for (k = 0; k < xs.length; k++) t += ys[k] * Math.pow(xs[k], i);
      A[i].push(t);
    }
    return gaussPivot(A);
  }

  /* ---------- sistemas lineares ---------- */

  /* Eliminação de Gauss com pivotamento parcial, sobre a matriz
     aumentada. Devolve a solução, ou null se o pivô ficar nulo. */
  function gaussPivot(Ab) {
    var n = Ab.length, i, j, k;
    var M = Ab.map(function (l) { return l.slice(); });
    for (k = 0; k < n; k++) {
      var p = k;
      for (i = k + 1; i < n; i++) if (Math.abs(M[i][k]) > Math.abs(M[p][k])) p = i;
      if (Math.abs(M[p][k]) < 1e-300) return null;
      var tmp = M[k]; M[k] = M[p]; M[p] = tmp;
      for (i = k + 1; i < n; i++) {
        var f = M[i][k] / M[k][k];
        for (j = k; j <= n; j++) M[i][j] -= f * M[k][j];
      }
    }
    var x = new Array(n).fill(0);
    for (i = n - 1; i >= 0; i--) {
      var s = M[i][n];
      for (j = i + 1; j < n; j++) s -= M[i][j] * x[j];
      x[i] = s / M[i][i];
    }
    return x;
  }

  /* ---------- integração ---------- */

  function trapezios(f, a, b, n) {
    var h = (b - a) / n, s = 0.5 * (f(a) + f(b));
    for (var i = 1; i < n; i++) s += f(a + i * h);
    return s * h;
  }

  function simpson(f, a, b, n) {
    if (n % 2) n++;
    var h = (b - a) / n, s = f(a) + f(b);
    for (var i = 1; i < n; i++) s += f(a + i * h) * (i % 2 ? 4 : 2);
    return s * h / 3;
  }

  /* Romberg: a extrapolação de Richardson aplicada aos trapézios. A
     primeira coluna é trapézio, a segunda é Simpson, e daí em diante
     são regras que não têm nome e convergem depressa. */
  function romberg(f, a, b, niveis) {
    var T = [[trapezios(f, a, b, 1)]];
    for (var i = 1; i < niveis; i++) {
      T.push([trapezios(f, a, b, Math.pow(2, i))]);
      for (var j = 1; j <= i; j++) {
        var q = Math.pow(4, j);
        T[i].push((q * T[i][j - 1] - T[i - 1][j - 1]) / (q - 1));
      }
    }
    return T;
  }

  /* Nós e pesos de Gauss-Legendre em [-1, 1], achados pelas raízes do
     polinômio de Legendre por Newton. */
  function gaussLegendre(n) {
    var no = [], peso = [];
    for (var i = 0; i < n; i++) {
      var x = Math.cos(Math.PI * (i + 0.75) / (n + 0.5)), dp = 0;
      for (var it = 0; it < 100; it++) {
        var p0 = 1, p1 = 0;
        for (var k = 0; k < n; k++) {
          var p2 = p1; p1 = p0;
          p0 = ((2 * k + 1) * x * p1 - k * p2) / (k + 1);
        }
        dp = n * (x * p0 - p1) / (x * x - 1);
        var dx = -p0 / dp;
        x += dx;
        if (Math.abs(dx) < 1e-15) break;
      }
      no.push(x);
      peso.push(2 / ((1 - x * x) * dp * dp));
    }
    return { no: no, peso: peso };
  }

  function quadraturaGauss(f, a, b, n) {
    var g = gaussLegendre(n), s = 0;
    var c = (b - a) / 2, d = (b + a) / 2;
    for (var i = 0; i < n; i++) s += g.peso[i] * f(c * g.no[i] + d);
    return c * s;
  }

  /* ---------- equações diferenciais ---------- */

  function euler(f, y0, t0, t1, n) {
    var h = (t1 - t0) / n, t = t0, y = y0.slice(), out = [[t, y.slice()]];
    for (var i = 0; i < n; i++) {
      var d = f(t, y);
      for (var j = 0; j < y.length; j++) y[j] += h * d[j];
      t += h;
      out.push([t, y.slice()]);
    }
    return out;
  }

  function rk4(f, y0, t0, t1, n) {
    var h = (t1 - t0) / n, t = t0, y = y0.slice(), out = [[t, y.slice()]];
    for (var i = 0; i < n; i++) {
      var k1 = f(t, y);
      var y2 = y.map(function (v, j) { return v + h / 2 * k1[j]; });
      var k2 = f(t + h / 2, y2);
      var y3 = y.map(function (v, j) { return v + h / 2 * k2[j]; });
      var k3 = f(t + h / 2, y3);
      var y4 = y.map(function (v, j) { return v + h * k3[j]; });
      var k4 = f(t + h, y4);
      for (var j = 0; j < y.length; j++) {
        y[j] += h / 6 * (k1[j] + 2 * k2[j] + 2 * k3[j] + k4[j]);
      }
      t += h;
      out.push([t, y.slice()]);
    }
    return out;
  }

  /* ---------- formatação ---------- */

  function fmt(x, casas) {
    if (!isFinite(x)) return '—';
    if (casas === undefined) casas = 3;
    var s = Math.abs(x) >= 1e5 || (Math.abs(x) < 1e-3 && x !== 0)
      ? x.toExponential(casas)
      : x.toFixed(casas);
    return s.replace('.', ',');
  }

  function pct(x, casas) {
    return fmt(100 * x, casas === undefined ? 2 : casas) + '%';
  }

  /* Notação científica com o expoente em HTML, para as tabelas. */
  function sci(x, casas) {
    if (x === 0) return '0';
    if (!isFinite(x)) return '—';
    var e = Math.floor(Math.log10(Math.abs(x)));
    var m = x / Math.pow(10, e);
    /* entre 0,1 e 1000 a notação científica atrapalha mais do que ajuda:
       "2,000·10^0" é pior de ler que "2" */
    if (e >= -1 && e <= 2) return fmt(x, casas === undefined ? 3 : casas);
    return fmt(m, casas === undefined ? 3 : casas) + '\u00b710<sup>' + e + '</sup>';
  }

  return {
    epsilonMaquina: epsilonMaquina, proximoFloat: proximoFloat, ulps: ulps,
    somaKahan: somaKahan, somaIngenua: somaIngenua,
    bissecao: bissecao, newton: newton, secante: secante, ordemMedida: ordemMedida,
    lagrange: lagrange, splineNatural: splineNatural,
    minimosQuadrados: minimosQuadrados, gaussPivot: gaussPivot,
    trapezios: trapezios, simpson: simpson, romberg: romberg,
    gaussLegendre: gaussLegendre, quadraturaGauss: quadraturaGauss,
    euler: euler, rk4: rk4,
    fmt: fmt, pct: pct, sci: sci
  };
})();

/* O resto do site chama o utilitário de F, por herança dos outros
   sites. Aqui ele é N, e este apelido evita reescrever tudo. */
var F = N;

/* ===================================================================
   Desenho em canvas — eixos, barras e curvas
   =================================================================== */
var G = (function () {

  /* A cor mestra do site é o grafite-ardósia, a única neutra da família
     de disciplinas. As demais são as cores de série dos gráficos, as
     mesmas dos outros sites, escolhidas para se distinguirem também em
     preto e branco e para quem não enxerga cor vermelha. Sendo a mestra
     neutra, ela não disputa com nenhuma delas. */
  var COR = {
    tinta: '#1b1f24', suave: '#5b6773', grade: '#e6e8ec',
    mestra: '#59636f', clara: '#aab3bd', vinho: '#8c2f39',
    bronze: '#a8601f', ambar: '#b5831f', roxo: '#6b4e8f',
    azul: '#2c5f8d', verde: '#2f7d5e', fundo: '#ffffff'
  };

  /* Prepara o canvas para telas de alta densidade */
  /* naoLimpar serve para desenhar um segundo painel sobre a mesma tela:
     mexer em cv.width apaga o conteudo, de modo que so redimensionamos
     quando a medida realmente muda. */
  function preparar(cv, altura, naoLimpar) {
    var larg = cv.clientWidth || cv.parentNode.clientWidth || 600;
    var alt = altura || Math.round(larg * 0.56);
    var dpr = window.devicePixelRatio || 1;
    var w = Math.round(larg * dpr), h = Math.round(alt * dpr);
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    cv.style.height = alt + 'px';
    var ct = cv.getContext('2d');
    ct.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!naoLimpar) {
      ct.clearRect(0, 0, larg, alt);
      ct.fillStyle = COR.fundo;
      ct.fillRect(0, 0, larg, alt);
    }
    return { ct: ct, L: larg, A: alt };
  }

  /* Cria um sistema de eixos. op: {xmin,xmax,ymin,ymax,rotX,rotY,formataX,formataY} */
  function eixos(cv, op) {
    var p = preparar(cv, op.altura, op.limpar === false);
    var ct = p.ct;
    var m = op.margem || { e: 60, d: 16, c: 14, b: 40 };
    var x0 = m.e, x1 = p.L - m.d, y0 = m.c, y1 = p.A - m.b;
    var xmin = op.xmin, xmax = op.xmax, ymin = op.ymin || 0, ymax = op.ymax;

    function X(v) { return x0 + (v - xmin) / (xmax - xmin) * (x1 - x0); }
    function Y(v) { return y1 - (v - ymin) / (ymax - ymin) * (y1 - y0); }

    ct.font = '11px system-ui, sans-serif';
    ct.textBaseline = 'middle';

    // grade horizontal + rótulos y
    var nY = op.divY || 5;
    ct.strokeStyle = COR.grade; ct.lineWidth = 1;
    ct.fillStyle = COR.suave; ct.textAlign = 'right';
    for (var i = 0; i <= nY; i++) {
      var v = ymin + (ymax - ymin) * i / nY, y = Math.round(Y(v)) + 0.5;
      ct.beginPath(); ct.moveTo(x0, y); ct.lineTo(x1, y); ct.stroke();
      var rot = op.formataY ? op.formataY(v) : (Math.abs(v) < 1e-9 ? '0' : v.toPrecision(2));
      ct.fillText(rot, x0 - 7, y);
    }

    // marcas x
    if (op.marcasX) {
      ct.textAlign = 'center'; ct.textBaseline = 'top';
      op.marcasX.forEach(function (t) {
        var x = X(t.v);
        if (x < x0 - 1 || x > x1 + 1) return;
        ct.strokeStyle = COR.grade;
        ct.beginPath(); ct.moveTo(x, y1); ct.lineTo(x, y1 + 4); ct.stroke();
        ct.fillStyle = COR.suave;
        ct.fillText(t.r, x, y1 + 7);
      });
    }

    // eixos
    ct.strokeStyle = COR.suave; ct.lineWidth = 1.2;
    ct.beginPath();
    ct.moveTo(x0, y0); ct.lineTo(x0, y1); ct.lineTo(x1, y1);
    ct.stroke();

    // títulos
    ct.fillStyle = COR.suave; ct.font = '600 11px system-ui, sans-serif';
    if (op.rotX) { ct.textAlign = 'center'; ct.textBaseline = 'bottom';
      ct.fillText(op.rotX, (x0 + x1) / 2, p.A - 2); }
    if (op.rotY) {
      /* o titulo do eixo y fica colado a margem esquerda do proprio painel,
         e nao do canvas, para que dois paineis lado a lado nao se sobreponham */
      ct.save(); ct.translate(Math.max(11, m.e - 49), (y0 + y1) / 2);
      ct.rotate(-Math.PI / 2);
      ct.textAlign = 'center'; ct.textBaseline = 'top'; ct.fillText(op.rotY, 0, 0); ct.restore();
    }

    return { ct: ct, X: X, Y: Y, x0: x0, x1: x1, y0: y0, y1: y1, L: p.L, A: p.A,
             xmin: xmin, xmax: xmax, ymin: ymin, ymax: ymax };
  }

  /* Barras discretas. dados = [{x,y}] */
  function barras(g, dados, cor, larguraRel) {
    var ct = g.ct, n = dados.length;
    if (!n) return;
    var passo = (g.x1 - g.x0) / (g.xmax - g.xmin);
    var w = Math.max(1.5, passo * (larguraRel === undefined ? 0.74 : larguraRel));
    ct.fillStyle = cor || COR.mestra;
    dados.forEach(function (d) {
      var x = g.X(d.x), y = g.Y(d.y), h = g.y1 - y;
      if (h <= 0) return;
      ct.fillRect(x - w / 2, y, w, h);
    });
  }

  /* Curva contínua a partir de f(x) */
  function curva(g, f, cor, espessura, tracejado) {
    var ct = g.ct, passos = 420;
    ct.save();
    ct.strokeStyle = cor || COR.vinho;
    ct.lineWidth = espessura || 2;
    if (tracejado) ct.setLineDash(tracejado);
    ct.beginPath();
    for (var i = 0; i <= passos; i++) {
      var x = g.xmin + (g.xmax - g.xmin) * i / passos, y = f(x);
      if (!isFinite(y)) continue;
      var px = g.X(x), py = g.Y(Math.max(g.ymin, Math.min(g.ymax, y)));
      if (i === 0) ct.moveTo(px, py); else ct.lineTo(px, py);
    }
    ct.stroke();
    ct.restore();
  }

  /* Área sob f(x) entre a e b */
  function area(g, f, a, b, cor) {
    var ct = g.ct, passos = 240;
    a = Math.max(a, g.xmin); b = Math.min(b, g.xmax);
    if (b <= a) return;
    ct.save();
    ct.fillStyle = cor || 'rgba(44,95,141,.26)';
    ct.beginPath();
    ct.moveTo(g.X(a), g.y1);
    for (var i = 0; i <= passos; i++) {
      var x = a + (b - a) * i / passos;
      ct.lineTo(g.X(x), g.Y(Math.max(g.ymin, Math.min(g.ymax, f(x)))));
    }
    ct.lineTo(g.X(b), g.y1);
    ct.closePath(); ct.fill();
    ct.restore();
  }

  /* Linha vertical marcada */
  function vertical(g, x, cor, rotulo, tracejado) {
    var ct = g.ct, px = g.X(x);
    if (px < g.x0 || px > g.x1) return;
    ct.save();
    ct.strokeStyle = cor || COR.vinho; ct.lineWidth = 1.6;
    ct.setLineDash(tracejado === false ? [] : [5, 4]);
    ct.beginPath(); ct.moveTo(px, g.y0); ct.lineTo(px, g.y1); ct.stroke();
    if (rotulo) {
      ct.setLineDash([]);
      ct.fillStyle = cor || COR.vinho;
      ct.font = '600 11px system-ui, sans-serif';
      ct.textAlign = 'center'; ct.textBaseline = 'top';
      ct.fillText(rotulo, px, g.y0 + 1);
    }
    ct.restore();
  }

  /* Legenda simples no canto superior direito */
  function legenda(g, itens) {
    var ct = g.ct, x = g.x1 - 8, y = g.y0 + 10;
    ct.save();
    ct.font = '11px system-ui, sans-serif';
    ct.textAlign = 'right'; ct.textBaseline = 'middle';
    itens.forEach(function (it, i) {
      var yy = y + i * 16;
      ct.fillStyle = COR.tinta;
      ct.fillText(it.texto, x - 16, yy);
      ct.fillStyle = it.cor;
      ct.fillRect(x - 12, yy - 4, 11, 8);
    });
    ct.restore();
  }

  /* Marcas inteiras espaçadas automaticamente */
  function marcasInteiras(min, max, maximoRotulos) {
    var n = max - min + 1, passo = Math.max(1, Math.ceil(n / (maximoRotulos || 12))), m = [];
    for (var v = min; v <= max; v += passo) m.push({ v: v, r: String(v) });
    return m;
  }

  function marcasLineares(min, max, qtd, casas) {
    var m = [];
    for (var i = 0; i <= qtd; i++) {
      var v = min + (max - min) * i / qtd;
      m.push({ v: v, r: v.toFixed(casas === undefined ? 1 : casas).replace('.', ',') });
    }
    return m;
  }

  return { COR: COR, preparar: preparar, eixos: eixos, barras: barras, curva: curva,
           area: area, vertical: vertical, legenda: legenda,
           marcasInteiras: marcasInteiras, marcasLineares: marcasLineares };
})();

/* Redesenha os widgets quando a janela muda de tamanho */
var _redesenhos = [];
function registrarRedesenho(f) { _redesenhos.push(f); f(); }
window.addEventListener('resize', (function () {
  var t;
  return function () {
    clearTimeout(t);
    t = setTimeout(function () { _redesenhos.forEach(function (f) { f(); }); }, 160);
  };
})());
