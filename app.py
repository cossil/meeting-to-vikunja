
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from logic import VikunjaClient, GeminiService, TaskProcessor, GlossaryManager
import voice_ui

# Configuração da página
st.set_page_config(page_title="MeetingToVikunja", page_icon="📝", layout="wide")

st.title("📝 MeetingToVikunja")

# Inicialização de serviços
def init_services():
    try:
        vikunja = VikunjaClient()
        gemini = GeminiService()
        return vikunja, gemini
    except Exception as e:
        st.error(f"Erro ao inicializar serviços: {e}")
        return None, None

vikunja, gemini = init_services()

# --- Mode Selector ---
st.sidebar.title("Navegação")
mode = st.sidebar.radio("Modo de Operação", ["File Upload", "Voice Agent (Beta)"])

if mode == "Voice Agent (Beta)":
    st.sidebar.divider()
    st.sidebar.subheader("🧠 Configuração do Agente")
    model_option = st.sidebar.radio(
        "Modelo de Inteligência",
        ["Gemini 3 Flash (Smart)", "Gemini 2.5 Flash (Fast)"]
    )
    
    # Map friendly names to API model IDs
    model_map = {
        "Gemini 3 Flash (Smart)": "gemini-3-flash-preview",
        "Gemini 2.5 Flash (Fast)": "gemini-2.5-flash"
    }
    
    selected_model = model_map[model_option]
    voice_ui.render_voice_interface(model_name=selected_model)

else:
    # --- Existing File Upload Logic ---
    st.markdown("### Ponte Inteligente: De Atas de Reunião para Tarefas no Vikunja")
    combined_text = "" # Ensure defined scope

    # Estado da sessão
    if 'tasks_df' not in st.session_state:
        st.session_state.tasks_df = pd.DataFrame()
    if 'user_list' not in st.session_state and vikunja:
        with st.spinner("Buscando lista de usuários do Vikunja..."):
            st.session_state.user_list = vikunja.fetch_users()

    # Configurações na Sidebar
    st.sidebar.header("🛠️ Configurações")
    meeting_date = st.sidebar.date_input("📅 Data da Reunião", value=datetime.today())

    custom_instructions = st.sidebar.text_area(
        "Instruções Extras para o AI",
        placeholder="Ex: Ignore a conversa sobre o almoço. Foque no contrato do INPI.",
        help="Dê dicas ao AI sobre o que focar ou ignorar nesta reunião específica."
    )

    # 1. New Feature: User Directory (Sidebar) - Improved visibility
    with st.sidebar.expander("👥 Diretório de Usuários", expanded=False):
        if 'user_list' not in st.session_state or not st.session_state.user_list:
            st.warning("Nenhum usuário carregado ou lista vazia.")
            if st.button("🔄 Carregar Usuários"):
                with st.spinner("Buscando usuários..."):
                    st.session_state.user_list = vikunja.fetch_users()
                st.rerun()
        else:
            users_display = pd.DataFrame(st.session_state.user_list)[['id', 'username', 'name']]
            st.dataframe(users_display, width="stretch", hide_index=True)
            if st.button("🔄 Atualizar Lista"):
                with st.spinner("Atualizando..."):
                    st.session_state.user_list = vikunja.fetch_users()
                st.rerun()

    # 2. New Feature: Glossary Management (Sidebar)
    with st.sidebar.expander("📚 Dicionário de Correção", expanded=False):
        glossary_mgr = GlossaryManager()
        glossary_dict = glossary_mgr.load()
        
        # Transform dict to DataFrame for editor
        glossary_data = [
            {"Termo Correto": k, "Variações/Erros": ", ".join(v)} 
            for k, v in glossary_dict.items()
        ]
        df_glossary = pd.DataFrame(glossary_data)
        
        edited_glossary = st.data_editor(
            df_glossary,
            column_config={
                "Termo Correto": st.column_config.TextColumn("Termo Correto", required=True),
                "Variações/Erros": st.column_config.TextColumn("Variações/Erros (separadas por vírgula)")
            },
            num_rows="dynamic",
            width="stretch",
            key="glossary_editor"
        )
        
        if st.button("💾 Salvar Glossário"):
            # Convert back to dict
            new_glossary = {}
            for _, row in edited_glossary.iterrows():
                correct_term = str(row["Termo Correto"]).strip()
                variations = [v.strip() for v in str(row["Variações/Erros"]).split(",") if v.strip()]
                if correct_term:
                    new_glossary[correct_term] = variations
            
            glossary_mgr.save(new_glossary)
            st.success("✅ Glossário atualizado com sucesso!")

    st.sidebar.divider()
    st.sidebar.info(f"Projeto Alvo ID: {os.getenv('TARGET_PROJECT_ID', '******')}")

    # Upload de arquivo
    uploaded_files = st.file_uploader(
        "Arraste e solte sua(s) ata(s) de reunião (.txt, .md, .docx)", 
        type=["txt", "md", "docx"],
        accept_multiple_files=True,
        help="Você pode selecionar vários arquivos para consolidar a mesma reunião."
    )

    if uploaded_files:
        st.write(f"**Arquivos selecionados ({len(uploaded_files)}):**")
        for f in uploaded_files:
            st.write(f"- {f.name}")
        
        # Processar todos os arquivos
        combined_text = ""
        for uploaded_file in uploaded_files:
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            file_text = TaskProcessor.extract_text_from_file(temp_path)
            combined_text += f"\n\n--- INÍCIO DO ARQUIVO: {uploaded_file.name} ---\n{file_text}\n--- FIM DO ARQUIVO: {uploaded_file.name} ---\n"
            os.remove(temp_path)

        # Verificação de tokens
        token_count = TaskProcessor.estimate_tokens(combined_text)
        if token_count > 30000:
            st.warning(f"⚠️ Atenção: O texto combinado é grande (aprox. {token_count} tokens).")
        else:
            st.info(f"📊 Contexto consolidado: aprox. {token_count} tokens.")

        if st.button("🚀 Analisar com Gemini"):
            with st.spinner("Analisando reunião e consolidando tarefas..."):
                if not combined_text.strip():
                    st.error("Os arquivos estão vazios ou não puderam ser lidos.")
                else:
                    tasks = gemini.analyze_meeting_notes(combined_text, meeting_date, custom_instructions)
                    if tasks:
                        # Aplicar fuzzy matching e IDs
                        for task in tasks:
                            assignee_name = task.get("assignee_name")
                            user_id = TaskProcessor.match_assignee(assignee_name, st.session_state.user_list)
                            task["assignee_id"] = user_id
                        
                        # Salvar no Session State como DataFrame para estabilidade
                        st.session_state.tasks_df = pd.DataFrame(tasks)
                        st.success(f"{len(tasks)} tarefas extraídas com sucesso!")
                    else:
                        st.error("O Gemini não retornou tarefas ou houve um erro no processamento.")

    # Área de Revisão Humana
    if not st.session_state.tasks_df.empty:
        st.divider()
        st.subheader("🛠️ Revisão de Tarefas")
        
        # Callback para salvar edições de volta ao session_state
        def save_edits():
            if "editor_state" in st.session_state:
                # st.data_editor keys: edited_rows, added_rows, deleted_rows
                # Mas é mais simples usar um key fixo e deixar o Streamlit gerenciar
                pass

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("Revise, edite ou remova tarefas antes de sincronizar.")
        with col2:
            if st.button("🔗 Vincular Sugestões do Gemini", help="Tenta associar os nomes extraídos pelo Gemini"):
                # Atualizar session_state.tasks_df diretamente
                for idx, row in st.session_state.tasks_df.iterrows():
                    if pd.isna(row.get("assignee_id")) or row.get("assignee_id") is None:
                        name = row.get("assignee_name")
                        user_id = TaskProcessor.match_assignee(name, st.session_state.user_list, threshold=50)
                        st.session_state.tasks_df.at[idx, "assignee_id"] = user_id
                st.rerun()

        # 3. UX Improvement: Unassigned Task Alert
        unassigned_count = st.session_state.tasks_df['assignee_id'].isna().sum()
        if unassigned_count > 0:
            st.warning(f"⚠️ Existem {unassigned_count} tarefas sem responsável definido!")

        # Mapeamento para visualização
        user_map = {u['id']: u.get('name') or u.get('username') for u in st.session_state.user_list}
        user_map[None] = "Não atribuído"
        
        # O data_editor usa a key 'tasks_editor' e atualiza o session_state automaticamente se configurado corretamente
        # No entanto, a forma mais robusta é ler do session_state e salvar o resultado
        
        st.session_state.tasks_df = st.data_editor(
            st.session_state.tasks_df,
            column_config={
                "title": st.column_config.TextColumn("Título", required=True),
                "description": st.column_config.TextColumn("Descrição"),
                "assignee_name": st.column_config.TextColumn("Nome Extraído (Gemini)", disabled=True),
                "assignee_id": st.column_config.SelectboxColumn(
                    "Responsável (Vikunja)",
                    options=[u['id'] for u in st.session_state.user_list],
                    format_func=lambda x: user_map.get(x, "Desconhecido")
                ),
                "priority": st.column_config.NumberColumn("Prioridade (1-5)", min_value=1, max_value=5, step=1),
                "due_date": st.column_config.TextColumn("Data de Entrega (YYYY-MM-DD)")
            },
            num_rows="dynamic",
            width="stretch",
            height=600,
            key="tasks_editor" # Key fixa para estabilidade
        )

        if st.button("📤 Sincronizar com Vikunja"):
            # 0. Sanitize Data (Crucial for JSON compliance)
            # Replace NaN with None so they become null in JSON
            sync_df = st.session_state.tasks_df.where(pd.notnull(st.session_state.tasks_df), None)
            
            # 2. Feature Restore: Local Backup (Critical)
            try:
                backup_dir = "C:\\Ai\\meeting_to_vikunja\\Docs"
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"report_{timestamp}.md"
                backup_path = os.path.join(backup_dir, backup_filename)
                
                with open(backup_path, "w", encoding="utf-8") as f:
                    f.write(f"# Relatório de Sincronização - {meeting_date.strftime('%d/%m/%Y')}\n\n")
                    f.write("## Tarefas Aprovadas\n\n")
                    f.write(sync_df.to_markdown(index=False))
                    f.write("\n\n## Texto Original da Reunião\n\n")
                    f.write(combined_text)
                
                st.info(f"💾 Backup local gerado: `{backup_filename}`")
            except Exception as e:
                st.error(f"Erro ao gerar backup: {e}")

            progress_bar = st.progress(0)
            status_text = st.empty()
            
            verified_tasks = sync_df.to_dict('records')
            total = len(verified_tasks)
            success_count = 0
            
            for i, task in enumerate(verified_tasks):
                status_text.text(f"Enviando: {task['title']}")
                if vikunja.create_task(task):
                    success_count += 1
                
                progress = (i + 1) / total
                progress_bar.progress(progress)
                time.sleep(0.05)
                
            status_text.empty()
            st.balloons()
            st.success(f"✓ {success_count} de {total} tarefas criadas no Vikunja!")
            
    elif not uploaded_files:
        st.info("Aguardando upload de arquivo para começar...")
