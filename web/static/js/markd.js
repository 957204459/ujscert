(function () {
  function riskyWarning(e) {
    if (!confirm('您将访问的网址「' + this.href +'」安全性未知,是否继续?'))
      e.preventDefault();
  }

  [].forEach.call(document.querySelectorAll('[data-render=markd]'), function (elem) {
    var markdown = elem.textContent;
    var parent = elem.parentNode;
    var tag = document.createElement.bind(document),
      text = document.createTextNode.bind(document);
    var fragment = document.createDocumentFragment();
    var container = tag('div');

    parent.insertBefore(container, elem);
    parent.removeChild(elem);
    parent = null;

    var DELIMITERS = '![]()';
    var BEGIN = 0,
      DELIM = 1,
      LINE_BREAK = 2,
      WHITE_SPACE = 3,
      CODE_QUOTE = 4,
      TOKEN = 5,
      END = 6;

    var state = LINE_BREAK;

    var token = '';
    var tokens = [{type: BEGIN, token: ''}];
    var i = 0, ch;
    var type;

    // tokenize
    while (i < markdown.length) {
      ch = markdown.charAt(i);
      if (DELIMITERS.indexOf(ch) > -1) {
        type = DELIM;
      } else if (ch === '\n') {
        type = LINE_BREAK;
      } else if (ch === '`') {
        type = CODE_QUOTE;
      } else if (ch.match(/\s/) && state != TOKEN) {
        type = WHITE_SPACE;
      } else {
        type = TOKEN;
      }
      if (type !== DELIM && type === state) {
        token += ch;
      } else if (type !== WHITE_SPACE) {
        tokens.push({type: state, token: token});
        token = ch;
        state = type;
      }
      ++i;
    }
    tokens.push({type: END, token: ''});

// generate
    var node, img;
    var
      INSIDE_ALT = 1,
      INSIDE_SRC = 2,
      INSIDE_PARAGRAPH = 3,
      INSIDE_INLINE_CODE = 4,
      INSIDE_BLOCK_CODE = 5;

    for (i = 0; i < tokens.length; i++) {
      token = tokens[i];
      switch (token.type) {
        case BEGIN:
          state = INSIDE_PARAGRAPH;
          node = tag('p');
          break;

        case TOKEN:
          if (state === INSIDE_ALT && img) {
            img.alt = token.token;
          } else if (state === INSIDE_SRC) {
            // normalize url
            var anchor = tag('a');
            anchor.href = token.token;

            if (!anchor.protocol.match(/(f|ht)tps?:/)) {
              anchor.protocol = location.protocol;
            }

            if (anchor.hostname !== location.hostname) {
              node.addEventListener('click', riskyWarning);
            }

            node.href = anchor.href;
            if (img) {
              img.src = anchor.href;
            }
          } else {
            node.appendChild(text(token.token));
          }

          break;

        case CODE_QUOTE:
          if (token.token.length == 1) { // inline
            if (state === INSIDE_INLINE_CODE) { // close
              node = parent;
              state = INSIDE_PARAGRAPH;
            } else { // open
              parent = node;
              node = tag('code');
              parent.appendChild(node);
              state = INSIDE_INLINE_CODE;
            }

          } else if (token.token.length > 2) {
            if (state === INSIDE_BLOCK_CODE) { // close
              fragment.appendChild(node);
              state = INSIDE_PARAGRAPH;
            } else { // open
              node = tag('pre');
              state = INSIDE_BLOCK_CODE;
            }
          }
          break;

        case DELIM:
          ch = token.token;

          if (ch === '[') {
            parent = node;
            node = tag('a');
            node.target = '_blank';
            if (i && tokens[i - 1].token === '!') {
              img = tag('img');
              img.className = 'img-fluid';
              node.appendChild(img);
            }
            state = INSIDE_ALT;
          } else if (ch === ']' && state === INSIDE_ALT && tokens[i + 1].token === '(') {
            state = INSIDE_SRC;
            ++i;
          } else if (ch === ')' && state === INSIDE_SRC) {
            parent.appendChild(node);
            img = null;
            node = parent;
            state = INSIDE_PARAGRAPH;
          }
          break;

        case LINE_BREAK:
          if (state == INSIDE_BLOCK_CODE) {
            node.appendChild(text(token.token));
          } else if (token.token.length > 1) {
            fragment.appendChild(node);
            node = tag('p');
          } else if (node) {
            node.appendChild(text(' '));
          }
          break;

        case END:
          if (node && node.textContent.length)
            fragment.appendChild(node);
      }
    }

    // commit
    container.appendChild(fragment);
  });

})();