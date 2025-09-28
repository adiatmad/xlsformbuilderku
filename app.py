import streamlit as st
import pandas as pd
from io import BytesIO
import uuid

# Konfigurasi halaman
st.set_page_config(page_title="XLSForm Builder", layout="wide")

# Inisialisasi state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'choices' not in st.session_state:
    st.session_state.choices = []
if 'editing_index' not in st.session_state:
    st.session_state.editing_index = None

# Header
st.title("📝 XLSForm Builder")
st.markdown("Buat formulir survei Anda dan unduh sebagai file XLSX untuk ODK/KoboToolbox")

# Sidebar untuk pengaturan
with st.sidebar:
    st.header("Pengaturan Formulir")
    form_title = st.text_input("Judul Formulir", value="Formulir Survei")
    form_id = st.text_input("ID Formulir", value="survey")
    
    st.markdown("---")
    st.markdown("### Panduan:")
    st.markdown("1. Tambahkan pertanyaan menggunakan formulir di utama")
    st.markdown("2. Untuk pertanyaan pilihan, tambahkan opsi di bagian bawah")
    st.markdown("3. Klik 'Unduh XLSForm' untuk menghasilkan file")

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
                    "hint": question_hint
                }
                
                if st.session_state.editing_index is not None:
                    st.session_state.questions[st.session_state.editing_index] = question_data
                    st.session_state.editing_index = None
                else:
                    st.session_state.questions.append(question_data)
                
                st.success("Pertanyaan berhasil disimpan!")

# Tampilkan daftar pertanyaan
if st.session_state.questions:
    st.subheader("Daftar Pertanyaan")
    questions_df = pd.DataFrame(st.session_state.questions)
    st.dataframe(questions_df[["type", "name", "label", "required"]])
    
    # Tombol aksi untuk setiap pertanyaan
    col1, col2 = st.columns(2)
    with col1:
        selected_question = st.selectbox(
            "Pilih pertanyaan untuk diedit/dihapus",
            range(len(st.session_state.questions)),
            format_func=lambda x: st.session_state.questions[x]["name"]
        )
    with col2:
        col_edit, col_delete = st.columns(2)
        with col_edit:
            if st.button("Edit"):
                st.session_state.editing_index = selected_question
                question = st.session_state.questions[selected_question]
                st.experimental_rerun()
        with col_delete:
            if st.button("Hapus"):
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

# Fungsi untuk membuat XLSForm
def create_xlsform():
    # Buat sheet survey
    survey_df = pd.DataFrame(st.session_state.questions)
    survey_df = survey_df[["type", "name", "label", "required", "constraint", "hint"]]
    
    # Buat sheet choices
    choices_df = pd.DataFrame(st.session_state.choices)
    if not choices_df.empty:
        choices_df = choices_df[["list_name", "name", "label", "filter"]]
    
    # Buat sheet settings
    settings_df = pd.DataFrame({
        "form_title": [form_title],
        "form_id": [form_id],
        "version": ["2023.1.0"]
    })
    
    # Buat Excel writer
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        survey_df.to_excel(writer, sheet_name='survey', index=False)
        if not choices_df.empty:
            choices_df.to_excel(writer, sheet_name='choices', index=False)
        settings_df.to_excel(writer, sheet_name='settings', index=False)
    
    output.seek(0)
    return output

# Tombol unduh
if st.session_state.questions:
    st.markdown("---")
    st.subheader("Unduh XLSForm")
    
    xls_file = create_xlsform()
    st.download_button(
        label="📥 Unduh XLSForm",
        data=xls_file,
        file_name=f"{form_id}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.success("Formulir siap diunduh! Gunakan file ini di ODK/KoboToolbox")

else:
    st.info("Tambahkan minimal satu pertanyaan untuk membuat formulir")