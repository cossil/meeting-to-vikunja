import streamlit as st
import uuid
import base64
import os
from voice_core import VoiceAgentService, VoiceTaskState
from logic import VikunjaClient, TaskProcessor

def init_voice_state():
    """Initialize session state for the Voice Agent."""
    if 'voice_service' not in st.session_state:
        try:
            st.session_state['voice_service'] = VoiceAgentService()
            # Only warmup on fresh service init
            st.session_state['voice_service'].warmup_tts()
        except Exception as e:
            st.error(f"Failed to initialize Voice Agent Service: {e}")
            return

    if 'voice_agent_history' not in st.session_state:
        st.session_state['voice_agent_history'] = []
        
        # --- First Move: Greeting (Optimized with Caching) ---
        service: VoiceAgentService = st.session_state['voice_service']
        greeting_text = "Olá! Sou o Assistente de Tarefas. O que vamos agendar hoje?"
        greeting_audio = None
        welcome_file = "welcome_fixed.wav"

        # Check cache
        if os.path.exists(welcome_file):
            try:
                with open(welcome_file, "rb") as f:
                    greeting_audio = f.read()
                # print("✅ Loaded cached greeting.")
            except Exception as e:
                 print(f"⚠️ Error reading cached greeting: {e}")
        
        # Check if generation is needed
        if not greeting_audio:
            greeting_audio = service.generate_speech(greeting_text)
            # Save to cache
            if greeting_audio:
                try:
                    with open(welcome_file, "wb") as f:
                        f.write(greeting_audio)
                    # print("💾 Saved greeting to cache.")
                except Exception as e:
                    print(f"⚠️ Error saving cached greeting: {e}")

        st.session_state['voice_agent_history'].append({
            "role": "assistant",
            "text": greeting_text,
            "audio": greeting_audio
        })

    if 'voice_task_state' not in st.session_state:
        # Initial empty state
        st.session_state['voice_task_state'] = VoiceTaskState().model_dump(by_alias=True)

    # Pre-fetch users for assignment logic if not already present (reusing app.py's state if available, or fetching new)
    if 'voice_user_list' not in st.session_state:
        try:
             # Use a fresh client just for the voice agent to be safe, or check session state
             client = VikunjaClient()
             st.session_state['voice_user_list'] = client.fetch_users()
        except Exception as e:
             print(f"Unable to fetch users: {e}")
             st.session_state['voice_user_list'] = []

def render_voice_interface(model_name: str = "gemini-3-flash-preview"):
    # --- Custom HTML/CSS for Chat Bubbles ---
    st.markdown("""
    <style>
    .user-bubble {
        background-color: #dcf8c6;
        color: black;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 70%;
        margin-left: auto; /* Pushes to right */
        text-align: right;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .agent-bubble {
        background-color: #ffffff;
        color: black;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 70%;
        margin-right: auto; /* Pushes to left */
        text-align: left;
        border: 1px solid #e0e0e0;
        box-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎙️ Voice Agent (Beta)")
    st.caption(f"Modelo Ativo: {model_name}")

    init_voice_state()
    service: VoiceAgentService = st.session_state.get('voice_service')

    if not service:
        st.error("Service not initialized.")
        return

    # --- Layout: Two Columns (Chat vs Task Card) ---
    col_chat, col_state = st.columns([1, 1])

    with col_state:
        st.subheader("📋 Ficha da Tarefa")
        current_state = st.session_state['voice_task_state']
        
        # Display nicely formatted JSON or a visual card
        st.json(current_state, expanded=True)
        
        # Visual indicators for missing info
        missing = current_state.get('missingInfo', [])
        if missing:
            st.warning(f"Faltando: {', '.join(missing)}")
        else:
            st.success("✨ Todas as informações coletadas!")
        
        st.divider()
        
        # --- Vikunja Integration (Adapter Pattern) ---
        if st.button("🚀 Enviar Tarefa para o Vikunja"):
            with st.spinner("Enviando para o Vikunja..."):
                try:
                    # 1. Adapt Pydantic dict to VikunjaClient expected dict
                    # VoiceTaskState keys: title, description, dueDate (alias), assignee
                    # VikunjaClient expects: title, description, due_date, assignee_id, priority
                    
                    adapter_payload = {
                        "title": current_state.get("title"),
                        "description": current_state.get("description"),
                        "due_date": current_state.get("dueDate"), # Voice uses alias
                        "priority": 1 # Default
                    }
                    
                    # 2. Resolve Assignee Name -> ID
                    assignee_name = current_state.get("assignee")
                    user_list = st.session_state.get('voice_user_list', [])
                    
                    if assignee_name:
                        matched_id = TaskProcessor.match_assignee(assignee_name, user_list)
                        if matched_id:
                            adapter_payload["assignee_id"] = matched_id
                        else:
                            st.warning(f"Aviso: Não consegui vincular '{assignee_name}' a um usuário do Vikunja.")
                    
                    # 3. Call Logic
                    client = VikunjaClient()
                    success = client.create_task(adapter_payload)
                    
                    if success:
                        st.balloons()
                        st.success("Tarefa criada com sucesso no Vikunja!")
                        
                        # 重 Reset State for next task
                        st.session_state['voice_task_state'] = VoiceTaskState().model_dump(by_alias=True)
                        st.session_state['voice_agent_history'] = [] # Clear chat? Or keep it? User might want to keep context.
                        # Let's keep chat history but reset task state so they can say "Mais uma tarefa"
                        
                        # Add system message to history indicating reset
                        reset_msg = "Tarefa enviada! Estou pronto para a próxima."
                        reset_audio = service.generate_speech(reset_msg)
                        st.session_state['voice_agent_history'].append({
                            "role": "assistant",
                            "text": reset_msg,
                            "audio": reset_audio
                        })
                        st.rerun()
                        
                    else:
                        st.error("Erro ao criar tarefa no Vikunja. Verifique o console.")
                        
                except Exception as e:
                    st.error(f"Erro na integração: {e}")


    with col_chat:
        st.subheader("Conversa")
        
        container = st.container(height=500)
        
        with container:
            # Display history using Custom HTML
            for idx, msg in enumerate(st.session_state['voice_agent_history']):
                role = msg['role']
                text = msg['text']
                
                if role == 'user':
                    st.markdown(f'<div class="user-bubble">{text}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="agent-bubble">{text}</div>', unsafe_allow_html=True)
                    # Render audio player immediately below the agent bubble
                    if msg.get('audio'):
                        is_last = (idx == len(st.session_state['voice_agent_history']) - 1)
                        st.audio(msg['audio'], format='audio/wav', autoplay=is_last)

        # Input Area by default
        audio_value = st.audio_input("Falar")
        text_value = st.chat_input("Digite uma mensagem...")

        if audio_value:
             # Handle Audio
            audio_bytes = audio_value.read()
            import hashlib
            audio_hash = hashlib.md5(audio_bytes).hexdigest()
            
            if st.session_state.get('last_audio_hash') != audio_hash:
                with st.spinner("Ouvindo..."):
                    st.session_state['voice_agent_history'].append({
                        "role": "user",
                        "text": "🎤 [Áudio Enviado]",
                        "audio": audio_bytes
                    })

                    response = service.process_audio_turn(
                        audio_bytes=audio_bytes,
                        current_task=st.session_state['voice_task_state'],
                        model_name=model_name
                    )

                    st.session_state['voice_task_state'] = response.updated_task.model_dump(by_alias=True)
                    
                    agent_audio = service.generate_speech(response.reply_text)
                    
                    st.session_state['voice_agent_history'].append({
                        "role": "assistant",
                        "text": response.reply_text,
                        "audio": agent_audio
                    })
                    
                    st.session_state['last_audio_hash'] = audio_hash
                    st.rerun()

        elif text_value:
            # Handle Text
            with st.spinner("Pensando..."):
                st.session_state['voice_agent_history'].append({
                    "role": "user",
                    "text": text_value,
                    "audio": None
                })
                
                response = service.process_text_turn(
                    text=text_value,
                    current_task=st.session_state['voice_task_state'],
                    model_name=model_name
                )
                
                st.session_state['voice_task_state'] = response.updated_task.model_dump(by_alias=True)
                
                agent_audio = service.generate_speech(response.reply_text)
                
                st.session_state['voice_agent_history'].append({
                    "role": "assistant",
                    "text": response.reply_text,
                    "audio": agent_audio
                })
                
                st.rerun()
