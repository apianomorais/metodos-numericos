/* ===================================================================
   widgets.js: simuladores e calculadoras interativas
   Uso nas páginas: <div data-widget="nome"></div>
   Métodos Numéricos / LFCA–URCA
   =================================================================== */

(function () {
  'use strict';

  /* ---------- utilitários de DOM ---------- */
  function el(tag, attrs, filhos) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else if (k === 'texto') n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (filhos || []).forEach(function (c) { n.appendChild(c); });
    return n;
  }

  function moldura(raiz, titulo) {
    raiz.classList.add('widget');
    raiz.appendChild(el('div', { class: 'widget-cabeca', texto: titulo }));
    var corpo = el('div', { class: 'widget-corpo' });
    raiz.appendChild(corpo);
    return corpo;
  }

  /* Devolve o <input type=range>, para que o chamador possa movê-lo por código. */
  function deslizante(pai, rot, min, max, passo, inicial, aoMudar, formata) {
    var campo = el('div', { class: 'campo' });
    var lab = el('label');
    var val = el('span', { class: 'valor' });
    var inp = el('input', { type: 'range', min: min, max: max, step: passo, value: inicial });
    function mostrar() {
      val.innerHTML = formata ? formata(Number(inp.value)) : String(inp.value).replace('.', ',');
    }
    lab.innerHTML = rot + ' ';
    lab.appendChild(val);
    campo.appendChild(lab);
    campo.appendChild(inp);
    pai.appendChild(campo);
    inp.addEventListener('input', function () { mostrar(); aoMudar(Number(inp.value)); });
    mostrar();
    return inp;
  }

  /* Botões mutuamente exclusivos. Devolve uma função que troca a seleção. */
  function opcoes(pai, lista, inicial, aoMudar) {
    var cx = el('div', { class: 'botoes' });
    var bs = lista.map(function (o, i) {
      var b = el('button', { type: 'button', texto: o.rot });
      if (i !== inicial) b.classList.add('sec');
      b.addEventListener('click', function () {
        bs.forEach(function (x) { x.classList.add('sec'); });
        b.classList.remove('sec');
        aoMudar(o.v, o);
      });
      cx.appendChild(b);
      return b;
    });
    pai.appendChild(cx);
    return function (i) { bs[i].click(); };
  }

  function cartoes(pai, lista) {
    var g = el('div', { class: 'grade-num' });
    lista.forEach(function (c) {
      g.appendChild(el('div', { class: 'cartao-num', html:
        '<span class="rot">' + c.rot + '</span><span class="val" data-k="' + c.k + '">·</span>' }));
    });
    pai.appendChild(g);
    var por = function (vals) {
      Object.keys(vals).forEach(function (k) {
        var n = g.querySelector('[data-k="' + k + '"]');
        if (n) n.innerHTML = vals[k];
      });
    };
    /* alguns widgets trocam de vista e precisam trocar os rotulos junto */
    por.rotular = function (rots) {
      var ns = g.querySelectorAll('.rot');
      rots.forEach(function (r, i) { if (ns[i]) ns[i].textContent = r; });
    };
    return por;
  }

  function tipografar(no) {
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([no]).catch(function () {});
    }
  }

  var REGISTRO = {};


  /* Seta com ponta, usada por quase todo widget de cinemática. */
  function seta(ct, xa, ya, xb, yb, cor, esp, tracejado) {
    var dx = xb - xa, dy = yb - ya, r = Math.sqrt(dx * dx + dy * dy);
    if (r < 1.5) return;
    var ux = dx / r, uy = dy / r, p = Math.min(8, r * 0.42);
    ct.save();
    ct.strokeStyle = cor; ct.fillStyle = cor;
    ct.lineWidth = esp || 2; ct.lineCap = 'round'; ct.lineJoin = 'round';
    if (tracejado) ct.setLineDash(tracejado);
    ct.beginPath(); ct.moveTo(xa, ya); ct.lineTo(xb - ux * p * 0.8, yb - uy * p * 0.8);
    ct.stroke();
    ct.setLineDash([]);
    ct.beginPath();
    ct.moveTo(xb, yb);
    ct.lineTo(xb - ux * p - uy * p * 0.46, yb - uy * p + ux * p * 0.46);
    ct.lineTo(xb - ux * p + uy * p * 0.46, yb - uy * p - ux * p * 0.46);
    ct.closePath(); ct.fill();
    ct.restore();
  }

  /* Rótulo com halo branco, legível por cima de qualquer desenho. */
  function rotulo(ct, texto, x, y, cor, al, bl, fonte, corHalo) {
    ct.save();
    ct.font = fonte || '600 11px system-ui, sans-serif';
    ct.textAlign = al || 'center'; ct.textBaseline = bl || 'middle';
    ct.lineJoin = 'round'; ct.lineWidth = 3.5; ct.strokeStyle = corHalo || '#fff';
    ct.strokeText(texto, x, y);
    ct.fillStyle = cor; ct.fillText(texto, x, y);
    ct.restore();
  }

  /* Uma tabela simples, para as saídas numéricas que são a matéria-prima
     desta disciplina. `cab` é a linha de cabeçalho e `linhas` é uma lista
     de listas; devolve uma função que troca o corpo sem refazer o
     cabeçalho, para que o widget possa redesenhar a cada movimento do
     deslizante sem piscar. */
  function tabela(pai, cab, classe) {
    var t = el('table', classe ? { class: classe } : null);
    var thead = el('thead');
    var tr = el('tr');
    cab.forEach(function (c) { tr.appendChild(el('th', { html: c })); });
    thead.appendChild(tr);
    t.appendChild(thead);
    var tb = el('tbody');
    t.appendChild(tb);
    pai.appendChild(t);
    return function (linhas) {
      tb.innerHTML = '';
      linhas.forEach(function (L) {
        var r = el('tr');
        if (L.classe) r.className = L.classe;
        (L.celulas || L).forEach(function (c) { r.appendChild(el('td', { html: String(c) })); });
        tb.appendChild(r);
      });
      tipografar(t);
    };
  }

  /* =================================================================
     1. A grade de ponto flutuante
     A frase "a grade fica mais grossa quando se afasta da origem" é
     fácil de dizer e difícil de acreditar enquanto não se vê. O widget
     desenha os floats representáveis em torno de um expoente escolhido,
     mostra o espaçamento absoluto crescendo e o relativo ficando
     parado, e deixa somar uma parcela para ver se ela cabe na grade ou
     é engolida pelo arredondamento.
     ================================================================= */
  REGISTRO.grade = function (raiz) {
    var corpo = moldura(raiz, 'A grade dos números representáveis');
    var cv = el('canvas');
    corpo.appendChild(cv);

    var expo = 0;        /* o expoente: a grade mostrada é a de [2^e, 2^(e+1)) */
    var logP = 0;        /* log10 da parcela a somar */

    deslizante(corpo, 'Região da reta, \\(2^{e}\\) com \\(e=\\):', -20, 60, 1, expo,
      function (v) { expo = v; desenhar(); },
      function (v) { return v + '   (' + N.sci(Math.pow(2, v), 2) + ')'; });
    deslizante(corpo, 'Parcela a somar:', -20, 20, 1, logP,
      function (v) { logP = v; desenhar(); },
      function (v) { return '10^' + v; });

    var mostrar = cartoes(corpo, [
      { rot: 'Espaçamento absoluto', k: 'abs' },
      { rot: 'Espaçamento relativo', k: 'rel' },
      { rot: 'A parcela cabe?', k: 'cabe' },
      { rot: 'Resultado da soma', k: 'soma' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    function desenhar() {
      var p = G.preparar(cv, Math.min(128, Math.max(108, cv.clientWidth * 0.16)));
      var ct = p.ct;
      var base = Math.pow(2, expo);
      var h = N.proximoFloat(base, Infinity) - base;   /* espaçamento ali */
      var parcela = Math.pow(10, logP);

      /* A reta de cima mostra dois intervalos vizinhos, [2^e, 2^(e+1)) e
         [2^(e+1), 2^(e+2)), com uma amostra dos floats de cada um. O
         número real de floats por intervalo é 2^52: desenhar todos é
         impossível, e por isso se desenha uma amostra uniforme, que
         preserva o que importa, que é a razão de 2 entre as duas. */
      var y = p.A * 0.52, x0 = 36, x1 = p.L - 20;
      var meio = (x0 + x1) / 2;
      ct.save();
      ct.strokeStyle = G.COR.suave; ct.lineWidth = 1.2;
      ct.beginPath(); ct.moveTo(x0, y); ct.lineTo(x1, y); ct.stroke();

      var nEsq = 16;
      var i;
      for (i = 0; i <= nEsq; i++) {
        var xx = x0 + (meio - x0) * i / nEsq;
        ct.strokeStyle = G.COR.mestra; ct.lineWidth = 1.4;
        ct.beginPath(); ct.moveTo(xx, y - 9); ct.lineTo(xx, y + 9); ct.stroke();
      }
      for (i = 1; i <= nEsq / 2; i++) {
        var xd = meio + (x1 - meio) * i / (nEsq / 2);
        ct.strokeStyle = G.COR.bronze; ct.lineWidth = 1.4;
        ct.beginPath(); ct.moveTo(xd, y - 9); ct.lineTo(xd, y + 9); ct.stroke();
      }
      ct.restore();

      rotulo(ct, '2^' + expo, x0, y + 24, G.COR.tinta, 'center');
      rotulo(ct, '2^' + (expo + 1), meio, y + 24, G.COR.tinta, 'center');
      rotulo(ct, '2^' + (expo + 2), x1, y + 24, G.COR.tinta, 'center');
      rotulo(ct, 'passo h', (x0 + meio) / 2, y - 18, G.COR.mestra, 'center');
      rotulo(ct, 'passo 2h', (meio + x1) / 2, y - 18, G.COR.bronze, 'center');
      rotulo(ct, 'a cada potência de dois o passo dobra, e o número de '
             + 'floats no intervalo é sempre o mesmo',
             p.L / 2, p.A - 8, '#6b7682', 'center', 'bottom');

      var soma = base + parcela;
      var cabe = soma !== base;
      mostrar({
        abs: N.sci(h, 3),
        rel: N.sci(h / base, 3),
        cabe: cabe ? 'sim' : 'não, some',
        soma: cabe ? (soma === base + parcela ? 'muda' : 'muda') : 'volta a 2^' + expo
      });

      var razao = parcela / h;
      var empate = Math.abs(razao - 0.5) < 1e-9;
      saida.innerHTML =
        'Em \\(2^{' + expo + '}\\) o passo da grade vale ' + N.sci(h, 3)
        + '. A parcela \\(10^{' + logP + '}\\) vale ' + N.sci(razao, 2)
        + ' passos. '
        + (empate
          ? 'Ela vale <strong>exatamente meio passo</strong>, e portanto o resultado '
            + 'cai bem no meio de dois floats vizinhos. O IEEE 754 desempata '
            + 'escolhendo o de mantissa <em>par</em>, que aqui é \\(2^{' + expo
            + '}\\), e por isso <code>' + base + ' + ' + parcela + ' == ' + base
            + '</code> devolve <code>True</code>. Com três em vez de um, o desempate '
            + 'cairia para o outro lado e a soma mudaria.'
          : cabe
            ? 'Ela passa de meio passo, então a soma muda o número: '
              + '<code>' + base + ' + ' + parcela + '</code> dá um float diferente.'
            : '<strong>Ela não chega a meio passo</strong>, cai no vão entre dois '
              + 'floats vizinhos e é arredondada de volta: <code>' + base + ' + '
              + parcela + ' == ' + base + '</code> devolve <code>True</code>. '
              + 'A parcela foi somada e não aconteceu nada.')
        + ' Repare na segunda ficha: o espaçamento <em>relativo</em> fica parado em '
        + '\\(2{,}22\\times10^{-16}\\) qualquer que seja o expoente, e é essa constância '
        + 'que faz o ponto flutuante ser útil: a precisão relativa não depende da '
        + 'escala em que se trabalha.';
      tipografar(saida);
      tipografar(raiz);
    }

    registrarRedesenho(desenhar);
  };


  /* =================================================================
     2. Newton: o passo e a bacia
     A primeira vista mostra de onde vem a convergência quadrática:
     a tangente, o ponto onde ela corta o eixo, e o erro encolhendo.
     A segunda mostra o preço disso. Pintando cada ponto de partida
     pela raiz a que ele leva, aparece uma estrutura que não tem nada
     de simples perto dos pontos críticos, e que é a razão de Newton
     precisar de chute bom. Com três raízes reais, "a raiz mais
     próxima" simplesmente não é a resposta.
     ================================================================= */
  REGISTRO.newton = function (raiz) {
    var corpo = moldura(raiz, 'O passo de Newton e a bacia de atração');
    var cv = el('canvas');
    corpo.appendChild(cv);

    var vista = 0, x0 = 2.6, passos = 0;

    /* f(x) = x^3 - 5x, com raízes em -raiz(5), 0 e +raiz(5), e derivada
       nula em +-raiz(5/3). É o caso mais simples em que Newton pode ir
       para qualquer uma das três. */
    function f(x) { return x * x * x - 5 * x; }
    function fl(x) { return 3 * x * x - 5; }
    var R5 = Math.sqrt(5), RC = Math.sqrt(5 / 3);
    var RAIZES = [-R5, 0, R5];
    var CORES = [G.COR.vinho, G.COR.mestra, G.COR.bronze];

    /* para onde Newton leva, a partir de x. Devolve o índice da raiz,
       ou -1 se não chegar a nenhuma. */
    function destino(x) {
      for (var k = 0; k < 60; k++) {
        var d = fl(x);
        if (d === 0 || !isFinite(x)) return -1;
        x = x - f(x) / d;
        if (Math.abs(x) > 1e6) return -1;
      }
      for (var i = 0; i < 3; i++) if (Math.abs(x - RAIZES[i]) < 1e-6) return i;
      return -1;
    }

    opcoes(corpo, [{ rot: 'Um passo de cada vez', v: 0 },
                   { rot: 'Bacia de atração', v: 1 }], 0,
      function (v) { vista = v; desenhar(); });

    var dx0 = deslizante(corpo, 'Ponto de partida \\(x_0\\):', -300, 300, 1,
      Math.round(x0 * 100),
      function (v) { x0 = v / 100; passos = 0; desenhar(); },
      function (v) { return N.fmt(v / 100, 2); });

    var linhaBotoes = el('div', { class: 'botoes' });
    var bPasso = el('button', { type: 'button', texto: 'Dar um passo' });
    var bZera = el('button', { type: 'button', class: 'sec', texto: 'Recomeçar' });
    bPasso.addEventListener('click', function () { passos++; desenhar(); });
    bZera.addEventListener('click', function () { passos = 0; desenhar(); });
    linhaBotoes.appendChild(bPasso);
    linhaBotoes.appendChild(bZera);
    corpo.appendChild(linhaBotoes);

    var mostrar = cartoes(corpo, [
      { rot: 'Passos dados', k: 'n' },
      { rot: '\\(x_n\\)', k: 'x' },
      { rot: 'Erro \\(|x_n-r|\\)', k: 'e' },
      { rot: 'Raiz alcançada', k: 'r' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    /* a sequência de iterados a partir de x0 */
    function iterados(n) {
      var seq = [x0], x = x0;
      for (var k = 0; k < n; k++) {
        var d = fl(x);
        if (d === 0 || !isFinite(x) || Math.abs(x) > 1e8) break;
        x = x - f(x) / d;
        seq.push(x);
      }
      return seq;
    }

    function desenhar() {
      var alt = vista === 0 ? 300 : 190;
      var p = G.preparar(cv, Math.min(alt, Math.max(alt * 0.8,
                                                    cv.clientWidth * 0.34)));
      var ct = p.ct;
      linhaBotoes.style.display = vista === 0 ? '' : 'none';

      var seq = iterados(passos);
      var xa = seq[seq.length - 1];
      var idx = destino(x0);

      if (vista === 0) {
        var g = G.eixos(cv, {
          altura: p.A, limpar: false,
          xmin: -3.2, xmax: 3.2, ymin: -9, ymax: 9,
          rotX: 'x', rotY: 'f(x)', divY: 6,
          margem: { e: 46, d: 16, c: 12, b: 34 },
          marcasX: [-3, -2, -1, 0, 1, 2, 3].map(function (t) {
            return { v: t, r: String(t) };
          })
        });
        /* a curva, traçada à mão porque G.curva corta no quadro */
        ct.save();
        ct.beginPath();
        for (var i = 0; i <= 400; i++) {
          var xx = -3.2 + 6.4 * i / 400, yy = f(xx);
          if (yy < -9 || yy > 9) { ct.moveTo(g.X(xx), g.Y(Math.max(-9, Math.min(9, yy)))); continue; }
          if (i === 0) ct.moveTo(g.X(xx), g.Y(yy)); else ct.lineTo(g.X(xx), g.Y(yy));
        }
        ct.strokeStyle = G.COR.tinta; ct.lineWidth = 2; ct.stroke();

        /* as três raízes */
        RAIZES.forEach(function (r, i) {
          ct.fillStyle = CORES[i];
          ct.beginPath(); ct.arc(g.X(r), g.Y(0), 4.5, 0, 2 * Math.PI); ct.fill();
        });
        /* onde a derivada se anula, que é onde o método escorrega */
        [-RC, RC].forEach(function (c) {
          ct.strokeStyle = '#c9ccd2'; ct.lineWidth = 1; ct.setLineDash([3, 3]);
          ct.beginPath(); ct.moveTo(g.X(c), g.y0); ct.lineTo(g.X(c), g.y1);
          ct.stroke(); ct.setLineDash([]);
        });

        /* as tangentes já percorridas, esmaecidas, e a próxima em destaque */
        for (i = 0; i < seq.length; i++) {
          var xv = seq[i];
          if (Math.abs(xv) > 3.2) continue;
          var ult = (i === seq.length - 1);
          var dv = fl(xv), prox = xv - f(xv) / dv;
          ct.strokeStyle = ult ? G.COR.roxo : '#d6d9de';
          ct.lineWidth = ult ? 1.8 : 1;
          ct.beginPath();
          ct.moveTo(g.X(xv), g.Y(f(xv)));
          ct.lineTo(g.X(Math.max(-3.2, Math.min(3.2, prox))), g.Y(0));
          ct.stroke();
          /* a vertical do ponto até a curva */
          ct.strokeStyle = ult ? G.COR.roxo : '#e3e6ea';
          ct.setLineDash([2, 3]);
          ct.beginPath(); ct.moveTo(g.X(xv), g.Y(0)); ct.lineTo(g.X(xv), g.Y(f(xv)));
          ct.stroke(); ct.setLineDash([]);
          ct.fillStyle = ult ? G.COR.roxo : '#b9bec6';
          ct.beginPath(); ct.arc(g.X(xv), g.Y(0), ult ? 4 : 2.5, 0, 2 * Math.PI);
          ct.fill();
        }
        ct.restore();
        rotulo(ct, 'x₀', g.X(x0), g.Y(0) + 17, G.COR.roxo, 'center');
        /* dentro do quadro e no alto, para nao bater na linha das marcas */
        rotulo(ct, 'f\u2032 = 0', g.X(RC) + 5, g.y0 + 10, '#9aa6b1', 'left');
        rotulo(ct, 'f\u2032 = 0', g.X(-RC) - 5, g.y0 + 10, '#9aa6b1', 'right');
      } else {
        /* a faixa das bacias: cada coluna de pixel é um ponto de partida */
        var y0b = p.A * 0.30, hb = p.A * 0.30;
        var L = p.L - 50, ox = 30;
        ct.save();
        for (var c = 0; c < L; c++) {
          var xs = -3.2 + 6.4 * c / (L - 1);
          var k2 = destino(xs);
          ct.fillStyle = k2 < 0 ? '#e9ecef' : CORES[k2];
          ct.fillRect(ox + c, y0b, 1, hb);
        }
        ct.restore();
        /* a escala e as raízes marcadas por baixo */
        var Xb = function (v) { return ox + (v + 3.2) / 6.4 * (L - 1); };
        ct.save();
        ct.strokeStyle = G.COR.tinta; ct.lineWidth = 1;
        ct.beginPath(); ct.moveTo(ox, y0b + hb); ct.lineTo(ox + L, y0b + hb);
        ct.stroke();
        [-3, -2, -1, 0, 1, 2, 3].forEach(function (t) {
          ct.beginPath(); ct.moveTo(Xb(t), y0b + hb); ct.lineTo(Xb(t), y0b + hb + 5);
          ct.stroke();
          rotulo(ct, String(t), Xb(t), y0b + hb + 17, G.COR.suave, 'center');
        });
        RAIZES.forEach(function (r, i) {
          ct.fillStyle = CORES[i];
          ct.beginPath(); ct.arc(Xb(r), y0b - 9, 4, 0, 2 * Math.PI); ct.fill();
        });
        /* o que importa aqui nao sao os pontos criticos, e sim a orbita
           de periodo 2 do mapa de Newton, em x = +-1: N(1) = -1 e
           N(-1) = 1. E nela que as faixas se acumulam. */
        [-1, 1].forEach(function (c2) {
          ct.strokeStyle = G.COR.tinta; ct.lineWidth = 1; ct.setLineDash([2, 2]);
          ct.beginPath(); ct.moveTo(Xb(c2), y0b - 4); ct.lineTo(Xb(c2), y0b + hb + 4);
          ct.stroke(); ct.setLineDash([]);
          rotulo(ct, 'ciclo 2', Xb(c2), y0b - 8, G.COR.tinta, 'center');
        });
        /* onde está o x0 escolhido */
        ct.strokeStyle = G.COR.tinta; ct.lineWidth = 2;
        ct.beginPath(); ct.moveTo(Xb(x0), y0b - 2); ct.lineTo(Xb(x0), y0b + hb + 2);
        ct.stroke();
        ct.restore();
        rotulo(ct, 'cada coluna é um ponto de partida, pintado com a cor da '
               + 'raiz a que Newton leva', p.L / 2, p.A - 6, '#6b7682',
               'center', 'bottom');
      }

      var nomes = ['−√5', '0', '+√5'];
      mostrar({
        n: String(passos),
        x: N.fmt(xa, 6),
        e: idx >= 0 ? N.sci(Math.abs(xa - RAIZES[idx]), 2) : '—',
        r: idx >= 0 ? nomes[idx] : 'nenhuma'
      });

      if (vista === 0) {
        var err = idx >= 0 ? Math.abs(xa - RAIZES[idx]) : NaN;
        saida.innerHTML =
          'A reta roxa é a tangente em \\(x_n\\); onde ela corta o eixo está '
          + '\\(x_{n+1}\\). Toda a ideia de Newton está aí: trocar a função pela sua '
          + 'tangente e resolver o problema linear, que é fácil. '
          + (passos === 0
            ? 'Clique em <em>Dar um passo</em> para ver o erro encolher.'
            : 'Repare no cartão do erro: a cada passo o número de zeros depois da '
              + 'vírgula praticamente <strong>dobra</strong>, e é isso que significa '
              + 'convergência quadrática.')
          + ' As duas verticais pontilhadas marcam onde \\(f\'=0\\): comece perto '
          + 'de uma delas e o primeiro passo joga o chute para longe.';
      } else {
        saida.innerHTML =
          'Cada coluna é um \\(x_0\\), pintado com a cor da raiz a que Newton chega. '
          + 'Na maior parte da reta a resposta é a esperada, e cada ponto vai para a '
          + 'raiz mais próxima. As exceções se concentram em \\(x=\\pm 1\\), e não '
          + 'nos pontos onde \\(f\'=0\\): ali está a <strong>órbita de período 2</strong> '
          + 'do mapa de Newton, \\(N(x)=2x^3/(3x^2-5)\\), que leva \\(1\\) em '
          + '\\(-1\\) e \\(-1\\) em \\(1\\). Ela é repelente, com multiplicador 36, '
          + 'e as faixas se acumulam sobre ela. '
          + 'Ampliando em torno de \\(x=1\\), aparecem de seis a sete faixas em '
          + '<em>cada</em> escala, de \\(10^{-1}\\) a \\(10^{-10}\\): a estrutura '
          + 'não termina. É o mesmo mecanismo do limiar do arco-tangente da seção 6, '
          + 'que também é uma órbita de período 2, e é por isso que um método robusto '
          + 'mantém sempre um intervalo com troca de sinal.';
      }
      tipografar(saida);
      tipografar(raiz);
      void dx0;
    }

    registrarRedesenho(desenhar);
  };


  /* =================================================================
     3. Runge, Chebyshev e a spline
     A frase "mais pontos pioram o resultado" é contraintuitiva o
     bastante para precisar ser vista. O widget põe as três curvas
     sobre a mesma função e deixa o aluno aumentar o grau: com nós
     uniformes o polinômio começa a oscilar nas bordas e sai da tela,
     com nós de Chebyshev ele melhora, e a spline simplesmente
     converge. A ficha do erro máximo transforma a impressão visual
     em número.
     ================================================================= */
  REGISTRO.runge = function (raiz) {
    var corpo = moldura(raiz, 'Interpolar a função de Runge');
    var cv = el('canvas');
    corpo.appendChild(cv);

    var n = 12, modo = 0;   /* 0 uniforme, 1 Chebyshev, 2 spline */

    function f(x) { return 1 / (1 + 25 * x * x); }

    function nosUnif(m) {
      var v = [];
      for (var i = 0; i <= m; i++) v.push(-1 + 2 * i / m);
      return v;
    }
    function nosCheb(m) {
      var v = [];
      for (var i = 0; i <= m; i++) v.push(Math.cos(Math.PI * i / m));
      return v.sort(function (a, b) { return a - b; });
    }

    opcoes(corpo, [{ rot: 'Nós uniformes', v: 0 },
                   { rot: 'Nós de Chebyshev', v: 1 },
                   { rot: 'Spline cúbica', v: 2 }], 0,
      function (v) { modo = v; desenhar(); });

    deslizante(corpo, 'Número de nós:', 4, 30, 2, n,
      function (v) { n = v; desenhar(); },
      function (v) { return (v + 1) + ' nós, grau ' + v; });

    var mostrar = cartoes(corpo, [
      { rot: 'Erro máximo', k: 'emax' },
      { rot: 'Erro no miolo', k: 'emeio' },
      { rot: 'Erro na borda', k: 'eborda' },
      { rot: 'Sai da tela?', k: 'sai' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    function desenhar() {
      var p = G.preparar(cv, Math.min(300, Math.max(230, cv.clientWidth * 0.32)));
      var xs = modo === 1 ? nosCheb(n) : nosUnif(n);
      var ys = xs.map(f);
      var aprox;
      if (modo === 2) {
        var sp = N.splineNatural(xs, ys);
        aprox = sp;
      } else {
        aprox = function (x) { return N.lagrange(xs, ys, x); };
      }

      var g = G.eixos(cv, {
        altura: p.A, limpar: false,
        xmin: -1.05, xmax: 1.05, ymin: -0.5, ymax: 1.5,
        rotX: 'x', rotY: 'f(x)', divY: 4,
        margem: { e: 50, d: 16, c: 12, b: 34 },
        marcasX: [-1, -0.5, 0, 0.5, 1].map(function (t) {
          return { v: t, r: N.fmt(t, 1) };
        })
      });
      var ct = g.ct;

      /* a função verdadeira */
      ct.save();
      ct.beginPath();
      for (var i = 0; i <= 600; i++) {
        var x = -1.05 + 2.1 * i / 600;
        if (i === 0) ct.moveTo(g.X(x), g.Y(f(x))); else ct.lineTo(g.X(x), g.Y(f(x)));
      }
      ct.strokeStyle = '#aab3bd'; ct.lineWidth = 3; ct.stroke();

      /* a aproximação, cortada no quadro mas sem fingir que ficou dentro */
      var emax = 0, emeio = 0, eborda = 0, saiu = false;
      ct.beginPath();
      var levantar = true;
      for (i = 0; i <= 900; i++) {
        x = -1 + 2 * i / 900;
        var v = aprox(x), e = Math.abs(v - f(x));
        if (e > emax) emax = e;
        if (Math.abs(x) < 0.5 && e > emeio) emeio = e;
        if (Math.abs(x) > 0.85 && e > eborda) eborda = e;
        if (v < -0.5 || v > 1.5) { saiu = true; levantar = true; continue; }
        if (levantar) { ct.moveTo(g.X(x), g.Y(v)); levantar = false; }
        else ct.lineTo(g.X(x), g.Y(v));
      }
      ct.strokeStyle = modo === 2 ? G.COR.verde : G.COR.vinho;
      ct.lineWidth = 2; ct.stroke();

      /* os nós */
      xs.forEach(function (xv, k) {
        ct.fillStyle = G.COR.mestra;
        ct.beginPath(); ct.arc(g.X(xv), g.Y(ys[k]), 3, 0, 2 * Math.PI); ct.fill();
      });
      ct.restore();

      /* legenda, sobre um fundo opaco: em grau alto a curva passa por
         cima dela e sem o fundo os dois textos se embaralham */
      ct.save();
      var itens = [{ cor: '#aab3bd', rot: '1/(1+25x²)' },
                   { cor: modo === 2 ? G.COR.verde : G.COR.vinho,
                     rot: modo === 2 ? 'spline' : 'polinômio' }];
      ct.fillStyle = 'rgba(255,255,255,0.88)';
      ct.fillRect(g.x0 + 6, g.y0 + 4, 104, 10 + itens.length * 15);
      itens.forEach(function (it, k) {
        var yy = g.y0 + 16 + k * 15;
        ct.fillStyle = it.cor; ct.fillRect(g.x0 + 12, yy - 4, 12, 4);
        rotulo(ct, it.rot, g.x0 + 29, yy, G.COR.tinta, 'left');
      });
      ct.restore();

      mostrar({
        emax: N.sci(emax, 2),
        emeio: N.sci(emeio, 2),
        eborda: N.sci(eborda, 2),
        sai: saiu ? 'sim' : 'não'
      });

      var txt;
      if (modo === 0) {
        txt = 'Com nós igualmente espaçados, aumente o grau e observe as duas fichas '
          + 'do meio andarem em <strong>direções opostas</strong>: o erro no miolo cai e '
          + 'o da borda cresce. É o fenômeno de Runge, e ele não é defeito de '
          + 'implementação nem acúmulo de arredondamento: o polinômio interpolador é '
          + 'único, e é ele mesmo que oscila. '
          + (saiu ? 'Neste grau a curva já sai do quadro; a parte que falta não foi '
                  + 'cortada por engano, ela está fora da escala.'
                  : 'Suba o grau até a curva sair do quadro.');
      } else if (modo === 1) {
        txt = 'Os mesmos grau e função, com os nós em \\(\\cos(k\\pi/n)\\), que se '
          + 'aglomeram nas bordas. Agora o erro cai quando o grau sobe, '
          + 'monotonicamente. A conclusão é que a culpa nunca foi do polinômio, e sim '
          + 'de <strong>onde se escolheu medir a função</strong>: as bordas precisavam '
          + 'de mais informação, e os nós uniformes davam a elas a mesma que ao miolo.';
      } else {
        txt = 'A spline cúbica usa um polinômio de grau 3 por intervalo, e por isso o '
          + 'grau não cresce com o número de nós: cresce o número de pedaços. Com os '
          + '<em>mesmos</em> nós uniformes em que o polinômio único explodia, ela '
          + 'converge. O preço está nos nós, onde a terceira derivada salta, e nas '
          + 'pontas, onde a condição natural impõe segunda derivada nula e rebaixa a '
          + 'ordem de \\(h^4\\) para \\(h^2\\).';
      }
      saida.innerHTML = txt;
      tipografar(saida);
      tipografar(raiz);
    }

    registrarRedesenho(desenhar);
  };


  /* =================================================================
     4. As regras de integração, e como elas convergem
     A primeira vista mostra o que cada regra faz com a função: o
     trapézio põe retas, Simpson põe parábolas, e Gauss põe pontos em
     lugares que não parecem ter lógica até que se veja o erro. A
     segunda transforma isso em retas num gráfico log-log, onde a
     ordem de cada método é literalmente a inclinação, e onde a queda
     exponencial de Gauss se distingue à primeira vista das potências
     de h.
     ================================================================= */
  REGISTRO.integracao = function (raiz) {
    var corpo = moldura(raiz, 'Trapézios, Simpson e Gauss');
    var cv = el('canvas');
    corpo.appendChild(cv);

    var regra = 0, nav = 5, vista = 0;
    var A = 0, B = Math.PI, EXATO = 2;
    function f(x) { return Math.sin(x); }

    opcoes(corpo, [{ rot: 'As regras', v: 0 },
                   { rot: 'Como convergem', v: 1 }], 0,
      function (v) { vista = v; desenhar(); });

    opcoes(corpo, [{ rot: 'Trapézios', v: 0 },
                   { rot: 'Simpson', v: 1 },
                   { rot: 'Gauss', v: 2 }], 0,
      function (v) { regra = v; desenhar(); });
    /* opcoes devolve um seletor, nao o no; a barra de botoes acabou de
       ser acrescentada, entao e a ultima do corpo */
    var barraRegra = corpo.querySelectorAll('.botoes');
    barraRegra = barraRegra[barraRegra.length - 1];

    var dN = deslizante(corpo, 'Avaliações da função:', 3, 15, 2, nav,
      function (v) { nav = v; desenhar(); },
      function (v) { return v + ' pontos'; });

    var mostrar = cartoes(corpo, [
      { rot: 'Valor obtido', k: 'val' },
      { rot: 'Erro', k: 'err' },
      { rot: 'Exato', k: 'ex' },
      { rot: 'Ordem do método', k: 'ord' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    /* as três regras, com k avaliações. Trapézio e Simpson usam k-1
       intervalos; Gauss usa k nós. */
    function aplicar(r, k) {
      if (r === 0) return N.trapezios(f, A, B, k - 1);
      if (r === 1) return N.simpson(f, A, B, k - 1);
      return N.quadraturaGauss(f, A, B, k);
    }

    function desenhar() {
      var p = G.preparar(cv, Math.min(280, Math.max(220, cv.clientWidth * 0.30)));
      barraRegra.style.display = vista === 0 ? '' : 'none';
      dN.parentNode.style.display = vista === 0 ? '' : 'none';

      if (vista === 0) {
        var g = G.eixos(cv, {
          altura: p.A, limpar: false,
          xmin: -0.15, xmax: Math.PI + 0.15, ymin: 0, ymax: 1.2,
          rotX: 'x', rotY: 'sen x', divY: 4,
          margem: { e: 58, d: 16, c: 12, b: 34 },
          formataY: function (v) { return v.toFixed(1); },
          marcasX: [{ v: 0, r: '0' }, { v: Math.PI / 2, r: 'π/2' },
                    { v: Math.PI, r: 'π' }]
        });
        var ct = g.ct, i;
        var k = nav;

        /* a área sob a regra, pintada */
        ct.save();
        if (regra === 0) {
          var h = (B - A) / (k - 1);
          for (i = 0; i < k - 1; i++) {
            var xa = A + i * h, xb = xa + h;
            ct.beginPath();
            ct.moveTo(g.X(xa), g.Y(0)); ct.lineTo(g.X(xa), g.Y(f(xa)));
            ct.lineTo(g.X(xb), g.Y(f(xb))); ct.lineTo(g.X(xb), g.Y(0));
            ct.closePath();
            ct.fillStyle = 'rgba(89,99,111,0.14)'; ct.fill();
            ct.strokeStyle = G.COR.mestra; ct.lineWidth = 1.4; ct.stroke();
          }
        } else if (regra === 1) {
          var np_ = k - 1;
          var h2 = (B - A) / np_;
          for (i = 0; i < np_; i += 2) {
            var x0 = A + i * h2, x1 = x0 + h2, x2 = x0 + 2 * h2;
            var y0 = f(x0), y1 = f(x1), y2 = f(x2);
            ct.beginPath();
            ct.moveTo(g.X(x0), g.Y(0));
            for (var t = 0; t <= 30; t++) {
              var xx = x0 + 2 * h2 * t / 30, s_ = (xx - x1) / h2;
              var yy = y1 + 0.5 * s_ * (y2 - y0) + 0.5 * s_ * s_ * (y2 - 2 * y1 + y0);
              ct.lineTo(g.X(xx), g.Y(yy));
            }
            ct.lineTo(g.X(x2), g.Y(0)); ct.closePath();
            ct.fillStyle = 'rgba(44,95,141,0.14)'; ct.fill();
            ct.strokeStyle = G.COR.azul; ct.lineWidth = 1.4; ct.stroke();
          }
        } else {
          var gl = N.gaussLegendre(k);
          var c = (B - A) / 2, d = (B + A) / 2;
          for (i = 0; i < k; i++) {
            var xg = c * gl.no[i] + d;
            var larg = gl.peso[i] * c;
            ct.fillStyle = 'rgba(168,96,31,0.16)';
            ct.fillRect(g.X(xg - larg / 2), g.Y(f(xg)),
                        g.X(larg) - g.X(0), g.Y(0) - g.Y(f(xg)));
            ct.strokeStyle = G.COR.bronze; ct.lineWidth = 1.2;
            ct.strokeRect(g.X(xg - larg / 2), g.Y(f(xg)),
                          g.X(larg) - g.X(0), g.Y(0) - g.Y(f(xg)));
          }
        }

        /* a função por cima */
        ct.beginPath();
        for (i = 0; i <= 400; i++) {
          var x = A + (B - A) * i / 400;
          if (i === 0) ct.moveTo(g.X(x), g.Y(f(x))); else ct.lineTo(g.X(x), g.Y(f(x)));
        }
        ct.strokeStyle = G.COR.tinta; ct.lineWidth = 2; ct.stroke();

        /* os pontos efetivamente avaliados */
        var pts = [];
        if (regra === 2) {
          var gl2 = N.gaussLegendre(k), c2 = (B - A) / 2, d2 = (B + A) / 2;
          for (i = 0; i < k; i++) pts.push(c2 * gl2.no[i] + d2);
        } else {
          for (i = 0; i < k; i++) pts.push(A + (B - A) * i / (k - 1));
        }
        pts.forEach(function (xv) {
          ct.fillStyle = G.COR.vinho;
          ct.beginPath(); ct.arc(g.X(xv), g.Y(f(xv)), 3.4, 0, 2 * Math.PI); ct.fill();
        });
        ct.restore();

        var v = aplicar(regra, k);
        mostrar({
          val: N.fmt(v, 8), err: N.sci(Math.abs(v - EXATO), 2),
          ex: '2', ord: ['2', '4', 'exponencial'][regra]
        });

        var nomes = ['retas', 'parábolas', 'retângulos de peso'];
        mostrar.rotular(['Valor obtido', 'Erro', 'Exato', 'Ordem do método']);
        saida.innerHTML =
          'Com ' + k + ' avaliações, a regra troca a função por ' + nomes[regra]
          + ' e integra isso. '
          + (regra === 2
            ? 'Repare que os pontos <strong>não estão igualmente espaçados</strong>, e '
              + 'que nenhum deles cai nas bordas. As posições foram escolhidas junto '
              + 'com os pesos, e é daí que vem a exatidão até grau \\(2n-1\\): com '
              + k + ' pontos, até grau ' + (2 * k - 1) + '. Subir o número de pontos '
              + 'sobe o grau, e é daí que vem o despencar do erro.'
            : 'Os pontos estão igualmente espaçados, e as bordas sempre entram. Cada '
              + 'pedaço da malha recebe o mesmo tratamento dos outros, de modo que a '
              + 'regra composta é exata só até grau <strong>'
              + (regra === 1 ? 3 : 1) + '</strong>, e segue sendo só até grau '
              + (regra === 1 ? 3 : 1) + ' com qualquer número de pontos: acrescentar '
              + 'avaliações encurta \\(h\\), não eleva o grau. Essa é a diferença de '
              + 'fundo para Gauss.')
          + ' Compare o erro das três com o mesmo número de pontos.';
      } else {
        /* log-log do erro contra avaliações */
        var ks = [], i2;
        for (i2 = 3; i2 <= 21; i2 += 2) ks.push(i2);
        var series = [0, 1, 2].map(function (r) {
          return ks.map(function (k) {
            return Math.max(Math.abs(aplicar(r, k) - EXATO), 1e-17);
          });
        });

        var g2 = G.eixos(cv, {
          altura: p.A, limpar: false,
          xmin: Math.log10(3), xmax: Math.log10(21),
          ymin: -17, ymax: 1,
          rotX: 'avaliações da função', rotY: 'log₁₀ do erro', divY: 6,
          margem: { e: 52, d: 16, c: 12, b: 36 },
          marcasX: [3, 5, 9, 15, 21].map(function (t) {
            return { v: Math.log10(t), r: String(t) };
          }),
          formataY: function (v) { return String(Math.round(v)); }
        });
        var ct2 = g2.ct;
        var cores = [G.COR.mestra, G.COR.azul, G.COR.bronze];
        var rots = ['trapézios', 'Simpson', 'Gauss'];
        ct2.save();
        series.forEach(function (e, r) {
          ct2.beginPath();
          e.forEach(function (v, j) {
            var X = g2.X(Math.log10(ks[j])), Y = g2.Y(Math.log10(v));
            if (j === 0) ct2.moveTo(X, Y); else ct2.lineTo(X, Y);
          });
          ct2.strokeStyle = cores[r]; ct2.lineWidth = 2; ct2.stroke();
          e.forEach(function (v, j) {
            ct2.fillStyle = cores[r];
            ct2.beginPath();
            ct2.arc(g2.X(Math.log10(ks[j])), g2.Y(Math.log10(v)), 2.6, 0, 2 * Math.PI);
            ct2.fill();
          });
        });
        /* legenda embaixo a esquerda: no alto ela cobria o inicio das retas */
        var ly = g2.y1 - 10 - 3 * 15;
        ct2.fillStyle = 'rgba(255,255,255,0.9)';
        ct2.fillRect(g2.x0 + 6, ly, 92, 8 + 3 * 15);
        rots.forEach(function (rt, r) {
          var yy = ly + 12 + r * 15;
          ct2.fillStyle = cores[r]; ct2.fillRect(g2.x0 + 12, yy - 4, 12, 4);
          rotulo(ct2, rt, g2.x0 + 29, yy, G.COR.tinta, 'left');
        });
        ct2.restore();

        /* A inclinação se mede no trecho assintótico (os cinco últimos pontos) e
           contra o passo h = π/(k-1), não contra o custo k: é assim que a ordem
           está definida. Medida contra k, esta mesma curva daria 2,13 e 4,27,
           porque o fator (1 - 1/k)^p só some devagar. */
        function incl(e) {
          var j1 = e.length - 1;
          while (j1 > 0 && e[j1] < 1e-15) j1--;
          var j0 = Math.max(0, j1 - 4), sx = 0, sy = 0, sxx = 0, sxy = 0, m = 0, j;
          for (j = j0; j <= j1; j++) {
            var Xj = Math.log10(ks[j] - 1), Yj = Math.log10(e[j]);
            sx += Xj; sy += Yj; sxx += Xj * Xj; sxy += Xj * Yj; m++;
          }
          return (m * sxy - sx * sy) / (m * sxx - sx * sx);
        }
        mostrar.rotular(['Inclinação, trapézios', 'Inclinação, Simpson',
                         'Previsto', 'Gauss']);
        mostrar({
          val: N.fmt(-incl(series[0]), 2), err: N.fmt(-incl(series[1]), 2),
          ex: '2 e 4', ord: '4·10⁻¹⁶ em 9'
        });

        saida.innerHTML =
          'Num gráfico log-log, um erro que cai como \\(h^p\\) é uma <strong>reta de '
          + 'inclinação \\(-p\\)</strong>, e é por isso que esta é a figura certa '
          + 'para ler a ordem de um método. As duas primeiras fichas trazem as '
          + 'inclinações medidas de trapézios e de Simpson, contra os 2 e 4 previstos. '
          + 'Elas saem do trecho final e são medidas contra o <strong>passo</strong> '
          + '\\(h=\\pi/(k-1)\\), que é como a ordem está definida; lidas contra o eixo '
          + 'horizontal desta figura, que conta <em>avaliações</em>, dariam 2,13 e 4,27, '
          + 'porque o fator \\((1-1/k)^p\\) só desaparece devagar.'
          + ' Gauss não é reta nenhuma: ele despenca e bate no piso da precisão de '
          + 'máquina com nove avaliações. Uma curva que <em>encurva para baixo</em> '
          + 'em log-log converge mais rápido que qualquer potência, e é isso que '
          + 'significa convergência exponencial.';
      }
      tipografar(saida);
      tipografar(raiz);
    }

    registrarRedesenho(desenhar);
  };


  /* ------------------------------------------------------------------
     O pendulo de amplitude grande: o projeto da aula 5. Duas vistas.
     A primeira mostra onde cada truncamento da serie deixa de valer; a
     segunda mostra por que a substituicao de Legendre e indispensavel.
     ------------------------------------------------------------------ */
  REGISTRO.pendulo = function (raiz) {
    var corpo = moldura(raiz, 'O período do pêndulo de amplitude grande');
    var cv = el('canvas');
    corpo.appendChild(cv);

    /* o grau inicial do deslizante e a amplitude tem de sair do MESMO
       numero, ou a ficha mostra 69 graus e calcula 68,75 */
    var GRAUS0 = 60;
    var vista = 0, grau = 2, t0 = GRAUS0 * Math.PI / 180;

    /* K(m) pela media aritmetico-geometrica: seis iteracoes bastam para
       o ultimo bit, e o resultado bate com ellipk do SciPy em 14 digitos */
    function ellipk(m) {
      var a = 1, b = Math.sqrt(1 - m), i, an, bn;
      for (i = 0; i < 60; i++) {
        an = (a + b) / 2; bn = Math.sqrt(a * b);
        if (Math.abs(an - bn) < 1e-17 * an) { a = an; break; }
        a = an; b = bn;
      }
      return Math.PI / (2 * a);
    }
    function exato(t) { var k = Math.sin(t / 2); return 2 / Math.PI * ellipk(k * k); }

    /* a serie que o SymPy devolve, truncada no grau pedido */
    var C = [[0, 1], [2, 1 / 16], [4, 11 / 3072], [6, 173 / 737280],
             [8, 22931 / 1321205760]];
    function serie(t, g) {
      var s = 0;
      C.forEach(function (c) { if (c[0] <= g) s += c[1] * Math.pow(t, c[0]); });
      return s;
    }

    /* trapezio na forma de Legendre, com n intervalos */
    function legendre(t, n) {
      var k = Math.sin(t / 2), h = (Math.PI / 2) / n, s = 0, i, ph;
      for (i = 0; i <= n; i++) {
        ph = i * h;
        var y = 1 / Math.sqrt(1 - k * k * Math.sin(ph) * Math.sin(ph));
        s += (i === 0 || i === n) ? y / 2 : y;
      }
      return 2 / Math.PI * h * s;
    }
    /* a integral original, com o ultimo ponto descartado por ser singular */
    function ingenua(t, n) {
      var h = t / n, s = 0, i, th;
      for (i = 0; i < n; i++) {
        th = i * h;
        var d = Math.cos(th) - Math.cos(t);
        var y = d > 0 ? 1 / Math.sqrt(d) : 0;
        s += (i === 0) ? y / 2 : y;
      }
      return Math.SQRT2 / Math.PI * h * s;
    }

    opcoes(corpo, [{ rot: 'O período', v: 0 },
                   { rot: 'Por que a substituição', v: 1 }], 0,
      function (v) { vista = v; desenhar(); });

    opcoes(corpo, [{ rot: 'série até θ²', v: 2 },
                   { rot: 'até θ⁴', v: 4 },
                   { rot: 'até θ⁸', v: 8 }], 2,
      function (v) { grau = v; desenhar(); });
    var barraGrau = corpo.querySelectorAll('.botoes');
    barraGrau = barraGrau[barraGrau.length - 1];

    var dT = deslizante(corpo, 'Amplitude:', 5, 179, 1, GRAUS0,
      function (v) { t0 = v * Math.PI / 180; desenhar(); },
      function (v) { return v + '°'; });

    var mostrar = cartoes(corpo, [
      { rot: 'T/T₀ exato', k: 'a' },
      { rot: 'série', k: 'b' },
      { rot: 'erro da série', k: 'c' },
      { rot: 'trapézio, 8 pontos', k: 'd' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    function desenhar() {
      var p = G.preparar(cv, Math.min(300, Math.max(230, cv.clientWidth * 0.32)));
      barraGrau.style.display = vista === 0 ? '' : 'none';
      var i, g, ct;

      if (vista === 0) {
        g = G.eixos(cv, {
          altura: p.A, limpar: false,
          xmin: 0, xmax: 180, ymin: 0.98, ymax: 2.4,
          rotX: 'amplitude θ₀ (graus)', rotY: 'T/T₀', divY: 4,
          margem: { e: 54, d: 14, c: 12, b: 36 },
          marcasX: [0, 45, 90, 135, 180].map(function (v) {
            return { v: v, r: String(v) + '°' };
          }),
          formataY: function (v) { return v.toFixed(1); }
        });
        ct = g.ct; ct.save();

        /* as truncagens da serie, da mais pobre a mais rica */
        [[2, G.COR.clara], [4, G.COR.ambar], [8, G.COR.azul]].forEach(function (par) {
          ct.beginPath();
          for (i = 0; i <= 300; i++) {
            var gr = 180 * i / 300, t = gr * Math.PI / 180;
            var y = Math.min(serie(t, par[0]), 3);
            if (i === 0) ct.moveTo(g.X(gr), g.Y(y)); else ct.lineTo(g.X(gr), g.Y(y));
          }
          ct.strokeStyle = par[1];
          ct.lineWidth = par[0] === grau ? 2.4 : 1.2;
          ct.setLineDash(par[0] === grau ? [] : [4, 3]);
          ct.stroke(); ct.setLineDash([]);
        });

        /* o valor exato, por cima de tudo */
        ct.beginPath();
        for (i = 0; i <= 400; i++) {
          var gr2 = 179.6 * i / 400, t2 = gr2 * Math.PI / 180;
          var y2 = Math.min(exato(t2), 3);
          if (i === 0) ct.moveTo(g.X(gr2), g.Y(y2)); else ct.lineTo(g.X(gr2), g.Y(y2));
        }
        ct.strokeStyle = G.COR.tinta; ct.lineWidth = 2.2; ct.stroke();

        /* a amplitude escolhida */
        var grx = t0 * 180 / Math.PI;
        ct.strokeStyle = G.COR.vinho; ct.lineWidth = 1.2; ct.setLineDash([3, 3]);
        ct.beginPath(); ct.moveTo(g.X(grx), g.y0); ct.lineTo(g.X(grx), g.y1);
        ct.stroke(); ct.setLineDash([]);
        ct.fillStyle = G.COR.vinho;
        ct.beginPath();
        ct.arc(g.X(grx), g.Y(Math.min(exato(t0), 2.4)), 4, 0, 2 * Math.PI);
        ct.fill();

        /* legenda */
        var itens = [['exato', G.COR.tinta], ['θ²', G.COR.clara],
                     ['θ⁴', G.COR.ambar], ['θ⁸', G.COR.azul]];
        ct.fillStyle = 'rgba(255,255,255,0.92)';
        ct.fillRect(g.x0 + 8, g.y0 + 6, 74, 10 + 4 * 14);
        itens.forEach(function (it, j) {
          var yy = g.y0 + 18 + j * 14;
          ct.fillStyle = it[1]; ct.fillRect(g.x0 + 14, yy - 4, 11, 3.5);
          rotulo(ct, it[0], g.x0 + 30, yy, G.COR.tinta, 'left');
        });
        ct.restore();

        var ex = exato(t0), se = serie(t0, grau);
        mostrar.rotular(['T/T₀ exato', 'série até θ' + (grau === 2 ? '²' :
                         grau === 4 ? '⁴' : '⁸'), 'erro da série',
                         'trapézio, 8 pontos']);
        mostrar({
          a: N.fmt(ex, 8), b: N.fmt(se, 8),
          c: N.pct(Math.abs(se - ex) / ex, 3),
          d: N.fmt(legendre(t0, 8), 8)
        });

        saida.innerHTML =
          'Em ' + Math.round(t0 * 180 / Math.PI) + '°, o período é '
          + N.pct(ex - 1, 2) + ' maior que o do livro-texto. A série de '
          + 'SymPy truncada no grau ' + grau + ' erra ' + N.pct(Math.abs(se - ex) / ex, 3)
          + '. Repare que as três truncagens se descolam da curva exata em '
          + 'pontos bem diferentes, e que <strong>nenhuma</strong> delas serve '
          + 'perto de 180°, onde o período diverge: série de potências nenhuma '
          + 'reproduz uma divergência logarítmica. A última ficha mostra que o '
          + 'trapézio com oito pontos, na forma substituída, acerta onde a série '
          + 'já desistiu.';
      } else {
        /* dois painéis: o integrando original e o substituído */
        g = G.eixos(cv, {
          altura: p.A, limpar: false,
          xmin: 0, xmax: 2, ymin: 0, ymax: 6,
          rotX: 'θ à esquerda, φ à direita', rotY: 'integrando',
          divY: 3, margem: { e: 50, d: 14, c: 12, b: 36 },
          marcasX: [{ v: 0, r: '0' }, { v: 0.95, r: 'θ₀' }, { v: 1.05, r: '0' },
                    { v: 1.525, r: 'π/4' }, { v: 2, r: 'π/2' }],
          formataY: function (v) { return v.toFixed(0); }
        });
        ct = g.ct; ct.save();
        /* recorta na moldura: a curva da esquerda sai pelo alto, e deve
           sair cortada em vez de desenhar um topo achatado falso */
        ct.beginPath();
        ct.rect(g.x0, g.y0, g.x1 - g.x0, g.y1 - g.y0);
        ct.clip();

        /* esquerda: 1/raiz(cos th - cos t0), que estoura em th = t0 */
        ct.beginPath();
        for (i = 0; i <= 300; i++) {
          var u = i / 300, th = u * t0;
          var d = Math.cos(th) - Math.cos(t0);
          var y3 = d > 0 ? Math.min(1 / Math.sqrt(d), 40) : 40;
          if (i === 0) ct.moveTo(g.X(u * 0.95), g.Y(y3));
          else ct.lineTo(g.X(u * 0.95), g.Y(y3));
        }
        ct.strokeStyle = G.COR.vinho; ct.lineWidth = 2.2; ct.stroke();

        /* direita: 1/raiz(1 - k^2 sen^2 phi), limitado */
        var k2 = Math.pow(Math.sin(t0 / 2), 2);
        ct.beginPath();
        for (i = 0; i <= 300; i++) {
          var v2 = i / 300, ph2 = v2 * Math.PI / 2;
          var y4 = 1 / Math.sqrt(1 - k2 * Math.sin(ph2) * Math.sin(ph2));
          if (i === 0) ct.moveTo(g.X(1.05 + 0.95 * v2), g.Y(y4));
          else ct.lineTo(g.X(1.05 + 0.95 * v2), g.Y(y4));
        }
        ct.strokeStyle = G.COR.verde; ct.lineWidth = 2.2; ct.stroke();

        /* a divisória entre os dois painéis */
        ct.strokeStyle = G.COR.clara; ct.lineWidth = 1;
        ct.beginPath(); ct.moveTo(g.X(1), g.y0); ct.lineTo(g.X(1), g.y1); ct.stroke();
        rotulo(ct, 'forma original', g.X(0.47), g.y0 + 14, G.COR.vinho, 'center');
        rotulo(ct, 'depois da substituição', g.X(1.52), g.y0 + 14, G.COR.verde,
               'center');
        ct.restore();

        var ex2 = exato(t0);
        mostrar.rotular(['exato', 'original, 512 pontos',
                         'substituída, 8 pontos', 'erro da original']);
        mostrar({
          a: N.fmt(ex2, 8), b: N.fmt(ingenua(t0, 512), 8),
          c: N.fmt(legendre(t0, 8), 8),
          d: N.sci(Math.abs(ingenua(t0, 512) - ex2), 2)
        });

        saida.innerHTML =
          'À esquerda, o integrando como ele sai da conservação de energia: '
          + 'ele vai a infinito na borda, porque é lá que o pêndulo para. '
          + 'Nenhuma regra desta aula tolera isso, e o trapézio, mesmo com '
          + '512 pontos, erra na segunda casa. À direita, o mesmo período '
          + 'depois da troca \\(\\sen(\\theta/2)=\\sen(\\theta_0/2)\\sen\\varphi\\): '
          + 'a função ficou limitada, suave, e simétrica nas duas pontas. '
          + 'O trapézio com <strong>oito</strong> pontos acerta todos os '
          + 'dígitos. A substituição não melhorou o método; ela consertou o '
          + 'problema que o método recebia.';
      }
      tipografar(saida);
    }

    registrarRedesenho(desenhar);
  };

  /* ------------------------------------------------------------------
     A expansao de 1/q numa base, com o periodo marcado. Tudo em
     aritmetica de inteiros: o resto vive em 0..q-1, de modo que a
     deteccao de periodo e exata e nao depende de tolerancia nenhuma.
     ------------------------------------------------------------------ */
  REGISTRO.bases = function (raiz) {
    var corpo = moldura(raiz, 'A expansão de 1/q, e onde ela se repete');
    var cv = el('canvas');
    corpo.appendChild(cv);

    var q = 10, base = 2;
    var SIM = '0123456789ABCDEF';

    function mdc(a, b) { while (b) { var t = a % b; a = b; b = t; } return a; }

    /* ordem multiplicativa de base modulo q, tirados os fatores comuns */
    function previsto(q, base) {
      var m = q, g;
      while ((g = mdc(m, base)) > 1) m /= g;
      if (m === 1) return 0;
      var k = 1, r = base % m;
      while (r !== 1) { r = (r * base) % m; k++; }
      return k;
    }

    /* expansao de 1/q: devolve digitos, inicio do periodo e tamanho */
    function expandir(q, base, maximo) {
      var r = 1, d = [], onde = {}, i;
      for (i = 0; i < maximo; i++) {
        if (r === 0) return { d: d, ini: -1, per: 0 };
        if (onde[r] !== undefined) return { d: d, ini: onde[r], per: i - onde[r] };
        onde[r] = i;
        var y = r * base;
        d.push(Math.floor(y / q));
        r = y % q;
      }
      return { d: d, ini: -1, per: -1 };
    }

    /* a expansao sem parar no periodo: expandir() devolve so ate o primeiro
       resto repetido, e para DESENHAR e preciso ver a repeticao acontecer */
    function brutos(q, base, n) {
      var r = 1, d = [], i;
      for (i = 0; i < n; i++) {
        var y = r * base;
        d.push(Math.floor(y / q));
        r = y % q;
      }
      return d;
    }

    opcoes(corpo, [{ rot: 'base 2', v: 2 }, { rot: 'base 3', v: 3 },
                   { rot: 'base 8', v: 8 }, { rot: 'base 10', v: 10 },
                   { rot: 'base 16', v: 16 }], 2,
      function (v) { base = v; desenhar(); });

    deslizante(corpo, 'A fração é 1/q, com q =', 2, 40, 1, 10,
      function (v) { q = v; desenhar(); });

    var mostrar = cartoes(corpo, [
      { rot: 'a expansão', k: 'a' },
      { rot: 'período previsto', k: 'b' },
      { rot: 'período medido', k: 'c' },
      { rot: 'antes de repetir', k: 'd' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    function desenhar() {
      var r = expandir(q, base, 120);
      var p = G.preparar(cv, Math.min(150, Math.max(118, cv.clientWidth * 0.15)));
      var ct = p.ct, L = p.L, A = p.A;
      ct.save();
      ct.clearRect(0, 0, L, A);

      /* quantos digitos mostrar: o pre-periodo mais tres periodos */
      var mostrarN = r.ini < 0 ? r.d.length
                   : Math.min(r.ini + 3 * r.per, 48);
      var dig = brutos(q, base, mostrarN);

      var esq = 16, cima = 58;
      var larg = Math.min(26, Math.max(13, (L - 2 * esq - 30) / mostrarN));
      var alt = 26;

      rotulo(ct, '1/' + q + ' na base ' + base + ' =', esq, 14,
             G.COR.tinta, 'left', 'middle', '600 13px system-ui, sans-serif');
      rotulo(ct, '0,', esq + 2, cima + alt / 2, G.COR.tinta, 'left', 'middle',
             '600 15px system-ui, sans-serif');

      var x0 = esq + 18;
      dig.forEach(function (d, i) {
        var x = x0 + i * larg;
        var dentro = r.ini >= 0 && i >= r.ini;
        var qual = dentro ? Math.floor((i - r.ini) / r.per) : -1;
        ct.fillStyle = !dentro ? '#eef0f3'
                     : (qual % 2 === 0 ? 'rgba(140,47,57,0.14)'
                                       : 'rgba(140,47,57,0.07)');
        ct.fillRect(x, cima, larg - 1.5, alt);
        rotulo(ct, SIM[d], x + (larg - 1.5) / 2, cima + alt / 2,
               dentro ? G.COR.vinho : G.COR.tinta, 'center', 'middle',
               '600 13px system-ui, sans-serif');
      });
      if (r.ini < 0) {
        rotulo(ct, 'fim', x0 + dig.length * larg + 6, cima + alt / 2,
               G.COR.verde, 'left', 'middle',
               '600 12px system-ui, sans-serif');
      } else {
        rotulo(ct, '…', x0 + mostrarN * larg + 4, cima + alt / 2,
               G.COR.suave, 'left', 'middle', '600 15px system-ui, sans-serif');
        /* a chave sob o primeiro periodo */
        var xa = x0 + r.ini * larg, xb = x0 + (r.ini + r.per) * larg - 1.5;
        ct.strokeStyle = G.COR.vinho; ct.lineWidth = 1.4;
        ct.beginPath();
        ct.moveTo(xa, cima + alt + 5); ct.lineTo(xa, cima + alt + 10);
        ct.lineTo(xb, cima + alt + 10); ct.lineTo(xb, cima + alt + 5);
        ct.stroke();
        rotulo(ct, 'período ' + r.per, (xa + xb) / 2, cima + alt + 24,
               G.COR.vinho, 'center', 'middle',
               '600 12px system-ui, sans-serif');
        if (r.ini > 0) {
          var xc = x0, xd = x0 + r.ini * larg - 1.5;
          ct.strokeStyle = G.COR.suave;
          ct.beginPath();
          ct.moveTo(xc, cima - 5); ct.lineTo(xc, cima - 10);
          ct.lineTo(xd, cima - 10); ct.lineTo(xd, cima - 5);
          ct.stroke();
          rotulo(ct, r.ini === 1 ? 'pré-período' : 'pré-período ' + r.ini,
                 (xc + xd) / 2, cima - 19, G.COR.suave, 'center', 'middle',
                 '600 12px system-ui, sans-serif');
        }
      }
      ct.restore();

      var prev = previsto(q, base);
      mostrar({
        a: r.ini < 0 ? 'finita' : 'dízima',
        b: prev === 0 ? '—' : String(prev),
        c: r.ini < 0 ? '—' : String(r.per),
        d: r.ini < 0 ? String(r.d.length) + ' dígitos' : String(r.ini)
      });

      var q2 = q, g;
      while ((g = (function (a, b) { while (b) { var t = a % b; a = b; b = t; }
                                     return a; })(q2, base)) > 1) q2 /= g;

      saida.innerHTML = r.ini < 0
        ? 'Todo fator primo de ' + q + ' divide ' + base + ', e por isso a conta '
          + 'termina: são ' + r.d.length + ' dígitos e acabou. Repare que isso '
          + 'depende das duas coisas ao mesmo tempo, a fração <em>e</em> a base. '
          + 'Mude a base e a mesma fração pode virar dízima.'
        : 'Tirando de ' + q + ' os fatores que ele tem em comum com ' + base
          + ', sobra ' + q2 + '. O período é a <strong>ordem multiplicativa</strong> '
          + 'de ' + base + ' módulo ' + q2 + ', isto é, o menor \\(k\\) com '
          + '\\(' + base + '^k \\equiv 1 \\pmod{' + q2 + '}\\), e vale ' + prev
          + '. A régua mede ' + r.per + '. '
          + (r.ini === 0 ? 'A repetição começa no primeiro dígito, porque não '
                         + 'havia fator comum a retirar.'
             : (r.ini === 1 ? 'O dígito antes da chave é o pré-período, e vem '
                            : 'Os ' + r.ini + ' dígitos antes da chave são o '
                              + 'pré-período, e vêm ')
               + 'do fator que foi retirado de ' + q + '.');
      tipografar(saida);
    }

    registrarRedesenho(desenhar);
  };

  /* ------------------------------------------------------------------
     O V da derivada numerica: truncamento descendo, arredondamento
     subindo, e o minimo onde os dois se cruzam. As retas teoricas sao
     desenhadas por cima para que o cruzamento seja visivel.
     ------------------------------------------------------------------ */
  REGISTRO.dilema = function (raiz) {
    var corpo = moldura(raiz, 'Refinar melhora, até parar de melhorar');
    var cv = el('canvas');
    corpo.appendChild(cv);

    var qual = 0, ke = 8;
    var EPS = 2.220446049250313e-16;

    var FUNCS = [
      { rot: 'sen x', f: Math.sin, d: Math.cos,
        d2: function (x) { return -Math.sin(x); }, x0: 1 },
      { rot: 'eˣ', f: Math.exp, d: Math.exp, d2: Math.exp, x0: 1 },
      { rot: 'x³', f: function (x) { return x * x * x; },
        d: function (x) { return 3 * x * x; },
        d2: function (x) { return 6 * x; }, x0: 1 }
    ];

    opcoes(corpo, FUNCS.map(function (o, i) { return { rot: o.rot, v: i }; }), 0,
      function (v) { qual = v; desenhar(); });

    deslizante(corpo, 'Marcar h =', 1, 16, 1, 8,
      function (v) { ke = v; desenhar(); },
      function (v) { return '10⁻' + v; });

    var mostrar = cartoes(corpo, [
      { rot: 'erro, progressiva', k: 'a' },
      { rot: 'erro, central', k: 'b' },
      { rot: 'melhor h visto, progr.', k: 'c' },
      { rot: 'melhor h visto, central', k: 'd' }
    ]);
    var saida = el('div', { class: 'saida' });
    corpo.appendChild(saida);

    function erros(o) {
      var hs = [], ep = [], ec = [], i;
      for (i = 1; i <= 16; i += 0.25) {
        var h = Math.pow(10, -i);
        hs.push(i);
        ep.push(Math.max(Math.abs((o.f(o.x0 + h) - o.f(o.x0)) / h - o.d(o.x0)), 1e-18));
        ec.push(Math.max(Math.abs((o.f(o.x0 + h) - o.f(o.x0 - h)) / (2 * h)
                                  - o.d(o.x0)), 1e-18));
      }
      return { hs: hs, ep: ep, ec: ec };
    }

    function desenhar() {
      var o = FUNCS[qual];
      var r = erros(o);
      var p = G.preparar(cv, Math.min(300, Math.max(230, cv.clientWidth * 0.32)));

      var g = G.eixos(cv, {
        altura: p.A, limpar: false,
        xmin: 0.8, xmax: 16.2, ymin: -13, ymax: 1,
        rotX: 'refinamento, −log₁₀ h  (refinar é ir para a direita)',
        rotY: 'log₁₀ do erro', divY: 7,
        margem: { e: 52, d: 16, c: 12, b: 36 },
        marcasX: [1, 4, 8, 12, 16].map(function (v) {
          return { v: v, r: '10⁻' + v };
        }),
        formataY: function (v) { return String(Math.round(v)); }
      });
      var ct = g.ct, i;
      ct.save();
      ct.beginPath();
      ct.rect(g.x0, g.y0, g.x1 - g.x0, g.y1 - g.y0);
      ct.clip();

      /* as retas teoricas: truncamento e arredondamento */
      var fx = Math.abs(o.f(o.x0)), d2 = Math.abs(o.d2(o.x0));
      [[function (h) { return h / 2 * d2; }, G.COR.clara, 'trunc. ~ h'],
       [function (h) { return h * h / 6 * d2; }, G.COR.ambar, 'trunc. ~ h²'],
       [function (h) { return EPS * fx / h; }, G.COR.verde, 'arred. ~ ε/h']
      ].forEach(function (par) {
        ct.beginPath();
        for (i = 0; i <= 120; i++) {
          var L = 0.8 + 15.4 * i / 120, h = Math.pow(10, -L);
          var Y = Math.log10(Math.max(par[0](h), 1e-20));
          if (i === 0) ct.moveTo(g.X(L), g.Y(Y)); else ct.lineTo(g.X(L), g.Y(Y));
        }
        ct.strokeStyle = par[1]; ct.lineWidth = 1.2;
        ct.setLineDash([4, 3]); ct.stroke(); ct.setLineDash([]);
      });

      /* as duas curvas medidas */
      [[r.ep, G.COR.mestra], [r.ec, G.COR.vinho]].forEach(function (par) {
        ct.beginPath();
        par[0].forEach(function (v, j) {
          var X = g.X(r.hs[j]), Y = g.Y(Math.log10(v));
          if (j === 0) ct.moveTo(X, Y); else ct.lineTo(X, Y);
        });
        ct.strokeStyle = par[1]; ct.lineWidth = 2.2; ct.stroke();
      });

      /* o h marcado */
      var hm = Math.pow(10, -ke);
      var epm = Math.abs((o.f(o.x0 + hm) - o.f(o.x0)) / hm - o.d(o.x0));
      var ecm = Math.abs((o.f(o.x0 + hm) - o.f(o.x0 - hm)) / (2 * hm) - o.d(o.x0));
      ct.strokeStyle = G.COR.tinta; ct.lineWidth = 1; ct.setLineDash([3, 3]);
      ct.beginPath(); ct.moveTo(g.X(ke), g.y0); ct.lineTo(g.X(ke), g.y1);
      ct.stroke(); ct.setLineDash([]);
      [[epm, G.COR.mestra], [ecm, G.COR.vinho]].forEach(function (par) {
        if (par[0] <= 0) return;
        ct.fillStyle = par[1];
        ct.beginPath();
        ct.arc(g.X(ke), g.Y(Math.log10(par[0])), 4, 0, 2 * Math.PI);
        ct.fill();
      });
      ct.restore();

      /* legenda */
      ct.save();
      var itens = [['progressiva', G.COR.mestra], ['central', G.COR.vinho],
                   ['~ h', G.COR.clara], ['~ h²', G.COR.ambar],
                   ['~ ε/h', G.COR.verde]];
      /* embaixo a esquerda: no alto a legenda cobria as duas curvas */
      var ly = g.y1 - 8 - itens.length * 14;
      ct.fillStyle = 'rgba(255,255,255,0.92)';
      ct.fillRect(g.x0 + 6, ly, 98, 6 + itens.length * 14);
      itens.forEach(function (it, j) {
        var yy = ly + 12 + j * 14;
        ct.fillStyle = it[1]; ct.fillRect(g.x0 + 12, yy - 4, 11, 3.5);
        rotulo(ct, it[0], g.x0 + 29, yy, G.COR.tinta, 'left');
      });
      ct.restore();

      /* onde cada curva tem o minimo */
      function melhor(v) {
        var j = 0, k;
        for (k = 1; k < v.length; k++) if (v[k] < v[j]) j = k;
        return Math.pow(10, -r.hs[j]);
      }
      mostrar({
        a: N.sci(epm, 2), b: N.sci(ecm, 2),
        c: N.sci(melhor(r.ep), 1), d: N.sci(melhor(r.ec), 1)
      });

      saida.innerHTML =
        'Refinar é andar para a direita. No começo manda o '
        + '<strong>truncamento</strong>, e cada curva desce colada à reta '
        + 'tracejada da sua ordem. Passado o vale manda o '
        + '<strong>arredondamento</strong>, que cresce como '
        + '\\(\\varepsilon/h\\) porque o numerador é uma subtração de quase '
        + 'iguais, e as duas curvas colapsam na mesma reta verde: dali em diante '
        + 'o método não importa mais, só a aritmética. O vale fica onde as duas '
        + 'se cruzam, em \\(\\sqrt{\\varepsilon}\\approx 10^{-8}\\) para a '
        + 'progressiva e em \\(\\varepsilon^{1/3}\\approx 6\\times10^{-6}\\) '
        + 'para a central. Arraste o marcador até 10⁻¹⁶ e veja o que acontece '
        + 'com quem pede precisão demais.';
      tipografar(saida);
    }

    registrarRedesenho(desenhar);
  };

/* ---------- inicialização ---------- */
  document.addEventListener('DOMContentLoaded', function () {
    Array.prototype.forEach.call(document.querySelectorAll('[data-widget]'), function (n) {
      var f = REGISTRO[n.getAttribute('data-widget')];
      if (f) {
        try { f(n); }
        catch (e) {
          n.innerHTML = '<div class="saida">Não foi possível carregar este componente.</div>';
          if (window.console) console.error(e);
        }
      }
    });
  });
})();
