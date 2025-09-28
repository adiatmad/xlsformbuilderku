import streamlit as st
import pandas as pd
from io import BytesIO
import uuid
import re

# Konfigurasi halaman
st.set_page_config(page_title="XLSForm Builder", layout="wide")

# Inisialisasi state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'choices' not in st.session_state:
    st.session_state.choices = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None
if 'preview_answers' not in st.session_state:
    st.session_state.preview_answers = {}

# Header
st.title("📝 XLSForm Builder")
st.markdown("Buat formulir survei Anda dengan fitur skip logic dan preview")

# Sidebar untuk pengaturan
with st.sidebar:
    st.header("Pengaturan Formulir")
    form_title = st.text_input("Judul Formulir", value="Formulir Survei")
    form_id = st.text_input("ID Formulir", value="survey")
    
    st.markdown("---")
    st.markdown("### Fitur:")
    st.markdown("- ✅ Skip Logic")
    st.markdown("- ✅ Preview Formulir")
    st.markdown("- ✅ Drag & Drop Urutan")

# Tab untuk navigasi
tab1, tab2, tab3 = st.tabs(["Builder", "Preview", "Settings"])

with tab1:
    # Form untuk menambah/mengedit pertanyaan
    with st.expander("Tambah/Edit Pertanyaan", expanded=True):
        with st.form("question_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                question_name = st.text_input("Nama Pertanyaan*", help="Nama unik tanpa spasi (cont: nama_lengkap)")
                question_label = st.text_input("Label Pertanyaan*", help="Teks yang muncul di formulir")
                question_type = st.selectbox(
                    "Tipe Pertanyaan*",
                    [
                        "text", "integer", "decimal", "date", "time", "dateTime",
                        "select_one", "select_multiple", "note", "image", "geopoint"
                    ],
                    help="Pilih tipe jawaban yang diinginkan"
                )
                
            with col2:
                question_required = st.checkbox("Wajib Diisi", value=True)
                question_constraint = st.text_input("Constraint", help="Contoh: .>0 and .<100")
                question_hint = st.text_input("Petunjuk", help="Teks bantuan untuk pengguna")
                question_relevant = st.text_input("Skip Logic", help="Contoh: ${pertanyaan_sebelumnya} = 'ya'")
            
            submitted = st.form_submit_button(
                "Simpan Pertanyaan" if st.session_state.editing_index is None else "Update Pertanyaan"
            )
            
            if submitted:
                if not question_name or not question_label:
                    st.error("Nama dan Label pertanyaan wajib diisi!")
                else:
                    question_data = {
                        "type": question_type,
                        "name": question_name,
                        "label": question_label,
                        "required": "yes" if question_required else "no",
                        "constraint": question_constraint,
                        "hint": question_hint,
                        "relevant": question_relevant
                    }
                    
                    if st.session_state.editing_index is not None:
                        st.session_state.questions[st.session_state.editing_index] = question_data
                        st.session_state.editing_index = None
                    else:
                        st.session_state.questions.append(question_data)
                    
                    st.success("Pertanyaan berhasil disimpan!")

    # Tampilkan daftar pertanyaan dengan drag & drop
    if st.session_state.questions:
        st.subheader("Daftar Pertanyaan")
        
        # Buat dataframe untuk ditampilkan
        questions_df = pd.DataFrame(st.session_state.questions)
        display_df = questions_df[["type", "name", "label", "required", "relevant"]].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df)
        
        # Drag & drop dengan tombol naik/turun
        st.markdown("### Atur Urutan Pertanyaan")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_question = st.selectbox(
                "Pilih pertanyaan",
                range(len(st.session_state.questions)),
                format_func=lambda x: f"{x+1}. {st.session_state.questions[x]['name']}"
            )
        
        with col2:
            col_up, col_down = st.columns(2)
            with col_up:
                if st.button("⬆️ Naik", disabled=selected_question == 0):
                    # Tukar dengan pertanyaan di atasnya
                    st.session_state.questions[selected_question], st.session_state.questions[selected_question-1] = \
                        st.session_state.questions[selected_question-1], st.session_state.questions[selected_question]
                    st.experimental_rerun()
            with col_down:
                if st.button("⬇️ Turun", disabled=selected_question == len(st.session_state.questions)-1):
                    # Tukar dengan pertanyaan di bawahnya
                    st.session_state.questions[selected_question], st.session_state.questions[selected_question+1] = \
                        st.session_state.questions[selected_question+1], st.session_state.questions[selected_question]
                    st.experimental_rerun()
        
        # Tombol edit dan hapus
        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("✏️ Edit Pertanyaan"):
                st.session_state.editing_index = selected_question
                question = st.session_state.questions[selected_question]
                st.experimental_rerun()
        with col_delete:
            if st.button("🗑️ Hapus Pertanyaan"):
                del st.session_state.questions[selected_question]
                st.experimental_rerun()

    # Form untuk menambahkan pilihan (untuk pertanyaan bertipe select)
    if any(q["type"] in ["select_one", "select_multiple"] for q in st.session_state.questions):
        st.subheader("Kelola Pilihan Jawaban")
        
        # Pilih pertanyaan bertipe pilihan
        select_questions = [q for q in st.session_state.questions if q["type"] in ["select_one", "select_multiple"]]
        selected_select = st.selectbox(
            "Pilih pertanyaan pilihan",
            range(len(select_questions)),
            format_func=lambda x: select_questions[x]["name"]
        )
        list_name = select_questions[selected_select]["name"]
        
        # Form tambah pilihan
        with st.form("choice_form"):
            col1, col2 = st.columns(2)
            with col1:
                choice_name = st.text_input("Nama Pilihan*", help="Kode unik (cont: ya)")
                choice_label = st.text_input("Label Pilihan*", help="Teks yang muncul di formulir")
            with col2:
                choice_filter = st.text_input("Filter", help="Filter untuk pilihan (opsional)")
            
            add_choice = st.form_submit_button("Tambah Pilihan")
            
            if add_choice:
                if not choice_name or not choice_label:
                    st.error("Nama dan Label pilihan wajib diisi!")
                else:
                    st.session_state.choices.append({
                        "list_name": list_name,
                        "name": choice_name,
                        "label": choice_label,
                        "filter": choice_filter
                    })
                    st.success("Pilihan berhasil ditambahkan!")
        
        # Tampilkan pilihan yang ada
        if st.session_state.choices:
            choices_df = pd.DataFrame(st.session_state.choices)
            st.dataframe(choices_df[choices_df["list_name"] == list_name])

with tab2:
    st.header("Preview Formulir")
    st.markdown("Simulasi tampilan formulir dengan skip logic")
    
    if not st.session_state.questions:
        st.info("Tambahkan pertanyaan terlebih dahulu untuk melihat preview")
    else:
        # Form untuk simulasi jawaban
        with st.form("preview_form"):
            st.subheader(form_title)
            
            # Tampilkan pertanyaan sesuai urutan
            for i, q in enumerate(st.session_state.questions):
                # Evaluasi skip logic
                show_question = True
                if q["relevant"]:
                    try:
                        # Ganti variabel dengan nilai dari session state
                        expr = q["relevant"]
                        for var, val in st.session_state.preview_answers.items():
                            expr = expr.replace(f"${{{var}}}", f"'{val}'")
                        
                        # Evaluasi ekspresi
                        if expr:
                            show_question = eval(expr)
                    except:
                        show_question = True
                
                if show_question:
                    # Tampilkan pertanyaan
                    st.markdown(f"**{i+1}. {q['label']}**")
                    if q["hint"]:
                        st.caption(q["hint"])
                    
                    # Tampilkan input sesuai tipe
                    if q["type"] == "text":
                        answer = st.text_input("", key=q["name"])
                    elif q["type"] == "integer":
                        answer = st.number_input("", step=1, key=q["name"])
                    elif q["type"] == "decimal":
                        answer = st.number_input("", step=0