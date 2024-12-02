'use strict';

document.addEventListener('DOMContentLoaded', function () {
  // Función para cargar las conversaciones
  async function loadConversations() {
    console.log('Iniciando carga de conversaciones...');
    try {
      const response = await fetch('/api/conversations/');
      const data = await response.json();
      console.log('Datos recibidos:', data);

      const chatList = document.getElementById('chat-list');
      if (!chatList) {
        console.error('No se encontró el elemento chat-list');
        return;
      }

      // Limpiar lista existente
      chatList.innerHTML = '<li class="chat-contact-list-item chat-list-item-0 d-none"><h6 class="text-muted mb-0">No Chats Found</h6></li>';

      if (data.conversations && data.conversations.length > 0) {
        console.log('Número de conversaciones:', data.conversations.length);
        
        data.conversations.forEach(conv => {
          console.log('Procesando conversación:', conv);
          
          // Crear elemento de la lista
          const li = document.createElement('li');
          li.className = 'chat-contact-list-item';
          li.innerHTML = `
            <a class="d-flex align-items-center">
              <div class="flex-shrink-0 avatar avatar-online">
                <span class="avatar-initial rounded-circle bg-label-primary">${conv.phone_number.toString().slice(0,2)}</span>
              </div>
              <div class="chat-contact-info flex-grow-1 ms-2">
                <h6 class="chat-contact-name text-truncate m-0">+${conv.phone_number}</h6>
                <p class="chat-contact-status text-muted text-truncate mb-0">${conv.chat_history}</p>
              </div>
              <small class="text-muted mb-0">Activo</small>
            </a>
          `;
          
          // Agregar evento click
          li.onclick = () => {
            console.log('Click en conversación:', conv);
            // Remover clase active de todas las conversaciones
            document.querySelectorAll('.chat-contact-list-item').forEach(item => {
              item.classList.remove('active');
            });
            // Agregar clase active a la conversación seleccionada
            li.classList.add('active');
            showChat(conv);
          };
          
          chatList.appendChild(li);
        });
      } else {
        console.log('No se encontraron conversaciones');
        document.querySelector('.chat-list-item-0').classList.remove('d-none');
      }
    } catch (error) {
      console.error('Error cargando conversaciones:', error);
    }
  }

  // Función para mostrar el chat
  function showChat(conversation) {
    console.log('Mostrando chat:', conversation);
    const chatHistory = document.querySelector('.chat-history');
    if (!chatHistory) {
      console.error('No se encontró el elemento chat-history');
      return;
    }

    chatHistory.innerHTML = '';

    try {
      const messages = typeof conversation.chat_history === 'string' 
        ? JSON.parse(conversation.chat_history) 
        : conversation.chat_history;

      console.log('Mensajes procesados:', messages);

      if (Array.isArray(messages)) {
        messages.forEach(msg => {
          const li = document.createElement('li');
          li.className = `chat-message ${msg.role === 'user' ? 'chat-message-right' : ''}`;
          li.innerHTML = `
            <div class="d-flex overflow-hidden">
              ${msg.role === 'user' ? 
                `<div class="chat-message-wrapper flex-grow-1">
                  <div class="chat-message-text">
                    <p class="mb-0">${msg.content}</p>
                  </div>
                  <div class="text-end text-muted mt-1">
                    <i class='ti ti-checks ti-xs me-1 text-success'></i>
                    <small>Enviado</small>
                  </div>
                </div>
                <div class="user-avatar flex-shrink-0 ms-3">
                  <div class="avatar avatar-sm">
                    <span class="avatar-initial rounded-circle bg-label-primary">U</span>
                  </div>
                </div>` : 
                `<div class="user-avatar flex-shrink-0 me-3">
                  <div class="avatar avatar-sm">
                    <span class="avatar-initial rounded-circle bg-label-success">A</span>
                  </div>
                </div>
                <div class="chat-message-wrapper flex-grow-1">
                  <div class="chat-message-text">
                    <p class="mb-0">${msg.content}</p>
                  </div>
                  <div class="text-muted mt-1">
                    <small>Recibido</small>
                  </div>
                </div>`
              }
            </div>
          `;
          chatHistory.appendChild(li);
        });
      }
    } catch (error) {
      console.error('Error mostrando mensajes:', error);
    }
  }

  // Iniciar carga de conversaciones
  loadConversations();
  
  // Actualizar cada 30 segundos
  setInterval(loadConversations, 30000);
});