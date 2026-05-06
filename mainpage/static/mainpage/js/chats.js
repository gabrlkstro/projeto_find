/* ==========================================================
   chats.js  —  Lista de Chats + Modal Chat Detail
   Salvar em: static/mainpage/js/chats.js
   ========================================================== */

(function () {
  'use strict';

  /* ----------------------------------------------------------
     ELEMENTOS
     ---------------------------------------------------------- */
  const backdrop      = document.getElementById('chatModalBackdrop');
  const modal         = document.getElementById('chatModal');
  const modalAvatar   = document.getElementById('modalAvatar');
  const modalUsername = document.getElementById('modalUsername');
  const modalItem     = document.getElementById('modalItemName');
  const modalDot      = document.getElementById('modalStatusDot');
  const modalBadge    = document.getElementById('modalStatusBadge');
  const modalLoading  = document.getElementById('modalLoading');
  const modalMessages = document.getElementById('modalMessages');
  const modalEmpty    = document.getElementById('modalEmptyState');
  const msgBox        = document.getElementById('modalMessagesBox');
  const closeBtn      = document.getElementById('modalCloseBtn');
  const msgForm       = document.getElementById('modalMsgForm');
  const textarea      = document.getElementById('modalConteudo');
  const sendBtn       = document.getElementById('modalSendBtn');
  const toast         = document.getElementById('chatErrorToast');
  const searchInput   = document.getElementById('chatSearch');
  const csrfToken     = document.querySelector('[name=csrfmiddlewaretoken]').value;

  /* URLs do chat aberto no momento */
  let urlMessages = null;
  let urlSend     = null;
  let pollTimer   = null;
  let lastSender  = null;

  /* ----------------------------------------------------------
     UTILS
     ---------------------------------------------------------- */
  function escapeHtml(text) {
    const d = document.createElement('div');
    d.innerText = text;
    return d.innerHTML;
  }

  function isNearBottom() {
    return (msgBox.scrollHeight - msgBox.scrollTop - msgBox.clientHeight) < 160;
  }

  function showError(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 2800);
  }

  /* ----------------------------------------------------------
     MODAL — abrir / fechar
     ---------------------------------------------------------- */
  function openModal(data) {
    /* Preenche header */
    modalAvatar.textContent   = data.avatar;
    modalUsername.textContent = data.username;
    modalItem.textContent     = data.item;

    const isAtivo = data.status === 'ativo';

    modalDot.className = 'modal-status-dot ' + (isAtivo ? 'dot-ativo' : 'dot-fechado');
    modalBadge.textContent = data.statusLabel;
    modalBadge.className   = 'modal-status-badge ' + (isAtivo ? 'msb-ativo' : 'msb-fechado');

    /* URLs */
    urlMessages = data.urlMessages;
    urlSend     = data.urlSend;

    /* Reset área de mensagens */
    modalMessages.innerHTML = '';
    modalEmpty.style.display   = 'none';
    modalLoading.style.display = 'flex';
    textarea.value = '';
    textarea.style.height = 'auto';
    sendBtn.disabled = true;
    lastSender = null;

    /* Abre o backdrop */
    backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';

    /* Carrega e inicia polling */
    loadMessages();
    pollTimer = setInterval(loadMessages, 2000);

    /* Foca no input */
    setTimeout(() => textarea.focus(), 280);
  }

  function closeModal() {
    backdrop.classList.remove('open');
    document.body.style.overflow = '';
    clearInterval(pollTimer);
    pollTimer = null;
    urlMessages = null;
    urlSend = null;
  }

  /* ----------------------------------------------------------
     MENSAGENS — carregar
     ---------------------------------------------------------- */
  async function loadMessages() {
    if (!urlMessages) return;

    try {
      const r    = await fetch(urlMessages);
      const data = await r.json();

      if (!r.ok) { showError(data.error || 'Erro ao carregar'); return; }

      /* Atualiza status se a API retornar */
      if (data.status) {
        const isAtivo = data.status === 'ativo';
        modalBadge.textContent = isAtivo ? 'Ativo' : 'Fechado';
        modalBadge.className   = 'modal-status-badge ' + (isAtivo ? 'msb-ativo' : 'msb-fechado');
        modalDot.className     = 'modal-status-dot '   + (isAtivo ? 'dot-ativo' : 'dot-fechado');
      }

      renderMessages(data.mensagens || []);
    } catch {
      showError('Sem conexão');
    }
  }

  /* ----------------------------------------------------------
     MENSAGENS — renderizar
     ---------------------------------------------------------- */
  function renderMessages(mensagens) {
    modalLoading.style.display = 'none';

    if (!mensagens.length) {
      modalEmpty.style.display   = 'flex';
      modalMessages.style.display = 'none';
      return;
    }

    modalEmpty.style.display    = 'none';
    modalMessages.style.display = 'flex';

    const stick = isNearBottom();
    modalMessages.innerHTML = '';
    lastSender = null;

    for (const m of mensagens) {
      const senderKey    = m.is_me ? '__me__' : m.remetente;
      const isGroupStart = senderKey !== lastSender;

      const wrap = document.createElement('div');
      wrap.className =
        'msg ' + (m.is_me ? 'me' : 'other') + (isGroupStart ? ' group-start' : '');

      wrap.innerHTML = `
        <div class="bubble">
          <div class="bubble-name">${isGroupStart && !m.is_me ? escapeHtml(m.remetente) : ''}</div>
          <div class="bubble-text">${escapeHtml(m.conteudo)}</div>
          <div class="bubble-footer">
            <span class="bubble-time">${escapeHtml(m.data_envio)}</span>
            ${m.is_me ? '<i class="bi bi-check2-all" style="font-size:.65rem;color:var(--brand-accent);opacity:.7;"></i>' : ''}
          </div>
        </div>`;

      modalMessages.appendChild(wrap);
      lastSender = senderKey;
    }

    if (stick) msgBox.scrollTop = msgBox.scrollHeight;
  }

  /* ----------------------------------------------------------
     MENSAGENS — enviar
     ---------------------------------------------------------- */
  msgForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const conteudo = textarea.value.trim();
    if (!conteudo || !urlSend) return;

    sendBtn.disabled = true;
    const body = new URLSearchParams();
    body.append('conteudo', conteudo);

    try {
      const r    = await fetch(urlSend, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'X-CSRFToken': csrfToken,
        },
        body: body.toString(),
      });
      const data = await r.json();
      if (!r.ok) { showError(data.error || 'Erro ao enviar'); return; }

      textarea.value = '';
      textarea.style.height = 'auto';
      await loadMessages();
      msgBox.scrollTop = msgBox.scrollHeight;
    } catch {
      showError('Erro de conexão');
    } finally {
      sendBtn.disabled = textarea.value.trim() === '';
    }
  });

  /* ----------------------------------------------------------
     TEXTAREA — auto-grow + habilitar botão
     ---------------------------------------------------------- */
  textarea.addEventListener('input', () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    sendBtn.disabled = textarea.value.trim() === '';
  });

  textarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!sendBtn.disabled) msgForm.requestSubmit();
    }
  });

  /* ----------------------------------------------------------
     FECHAR MODAL
     ---------------------------------------------------------- */
  closeBtn.addEventListener('click', closeModal);

  /* Clique fora do modal (no backdrop) */
  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) closeModal();
  });

  /* Tecla Escape */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && backdrop.classList.contains('open')) closeModal();
  });

  /* ----------------------------------------------------------
     ABRIR MODAL ao clicar numa linha
     ---------------------------------------------------------- */
  document.querySelectorAll('.chat-row').forEach((row) => {
    row.addEventListener('click', () => {
      openModal({
        avatar:      row.dataset.avatar,
        username:    row.dataset.username,
        item:        row.dataset.item,
        status:      row.dataset.status,
        statusLabel: row.dataset.statusLabel,
        urlMessages: row.dataset.urlMessages,
        urlSend:     row.dataset.urlSend,
      });
    });
  });

  /* ----------------------------------------------------------
     BUSCA AO VIVO
     ---------------------------------------------------------- */
  if (searchInput) {
    searchInput.addEventListener('input', function () {
      const q = this.value.toLowerCase();
      document.querySelectorAll('.chat-row').forEach((row) => {
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }
})();