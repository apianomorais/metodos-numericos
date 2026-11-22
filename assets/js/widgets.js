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
