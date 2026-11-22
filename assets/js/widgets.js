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
    return function (vals) {
      Object.keys(vals).forEach(function (k) {
        var n = g.querySelector('[data-k="' + k + '"]');
        if (n) n.innerHTML = vals[k];
      });
    };
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
