# TODO - Organização e Limpeza do Projeto FIND

## Passos

- [x] 1. Analisar arquivos e identificar problemas
- [x] 2. Apagar CSS não utilizados:
  - `mainpage/static/mainpage/css/cadastrar-item.css`
  - `mainpage/static/mainpage/css/register_item.css`
  - `mainpage/static/mainpage/css/style.css`
  - `mainpage/static/mainpage/css/chats_list.css`
  - `mainpage/static/mainpage/css/edit_profile.css`
- [x] 3. Renomear `item_delete.html` → `item_confirm_delete.html` e adaptar conteúdo
- [x] 4. Criar template ausente `chat_detail.html`
- [x] 5. Corrigir referência de imagem em `user.html` (user.png → user.webp)
- [x] 6. Corrigir referência de imagem em `edit_profile.html` (img/default-user.png → mainpage/img/user.webp)
- [x] 7. Extrair CSS inline de templates para arquivos CSS:
  - `chat_detail.html` → `chat_detail.css`
  - `item_confirm_delete.html` → `item_confirm_delete.css`
  - `edit_profile.html` → `edit_profile.css`
  - `item_detail.html` botão desabilitado → `item_detail.css`
  - `chats_list.html` modal styles → `chats.css`
- [x] 8. Testar servidor Django (`python manage.py check` — sem erros)

