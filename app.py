# app.py
import streamlit as st
from pyxform.builder import create_survey_from_dict
import tempfile
from st_sortable import sortable_list

st.set_page_config(page_title="XLSForm Builder Ultimate", layout="wide")
st.title("XLSForm Builder – Versi Ultimate (Kobo-style)")

# Initialize state
if "questions" not in st.session_state:
    st.session_state.questions = []

# --- Sidebar: Tambah Pertanyaan Baru ---
with st.sidebar.expander("Tambah Pertanyaan Baru"):
    q_text = st.text_input("Teks Pertanyaan")
    q_name = st.text_input("Nama Variabel (unique, tanpa spasi)")
    q_type = st.selectbox("Tipe Jawaban", ["text", "integer", "select_one", "select_multiple"])
    q_choices = st.text_area("Pilihan Jawaban (pisahkan koma, untuk select types)").strip()
    add_skip = st.checkbox("Tambahkan Skip Logic?")
    skip_condition = st.text_input("Tampilkan pertanyaan ini jika jawaban sebelumnya = ...") if add_skip else None

    if st.button("Tambah Pertanyaan"):
        if not q_name or not q_text:
            st.warning("Nama variabel dan teks pertanyaan wajib diisi!")
        else:
            choices_list = [c.strip() for c in q_choices.split(",")] if q_choices else None
            st.session_state.questions.append({
                "name": q_name,
                "label": q_text,
                "type": q_type,
                "choices": choices_list,
                "skip": skip_condition
            })
            st.success(f"Pertanyaan '{q_text}' ditambahkan!")

# --- Main: Drag & Drop + Live Preview ---
st.subheader("Live Preview & Drag & Drop Urutan")

if st.session_state.questions:
    # Buat label untuk sortable
    question_labels = [f"{i+1}. {q['label']} ({q['type']})" for i, q in enumerate(st.session_state.questions)]
    new_order = sortable_list(question_labels)
    
    # Reorder questions
    st.session_state.questions = [st.session_state.questions[i] for i in new_order]

    # Live preview interaktif
    st.markdown("**Preview Form:**")
    for idx, q in enumerate(st.session_state.questions):
        st.markdown(f"**{idx+1}. {q['label']}** ({q['type']})" + (f" – skip if {q['skip']}" if q['skip'] else ""))
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Hapus", key=f"del_{idx}"):
                st.session_state.questions.pop(idx)
                st.experimental_rerun()
        with col2:
            if st.button("Edit", key=f"edit_{idx}"):
                q_edit_text = st.text_input("Teks Pertanyaan", value=q["label"], key=f"edit_text_{idx}")
                q_edit_type = st.selectbox("Tipe Jawaban", ["text", "integer", "select_one", "select_multiple"], index=["text","integer","select_one","select_multiple"].index(q["type"]), key=f"edit_type_{idx}")
                q_edit_choices = st.text_area("Pilihan Jawaban", value=", ".join(q["choices"]) if q["choices"] else "", key=f"edit_choices_{idx}")
                q_edit_skip = st.text_input("Skip Logic", value=q["skip"] if q["skip"] else "", key=f"edit_skip_{idx}")
                if st.button("Simpan Edit", key=f"save_{idx}"):
                    st.session_state.questions[idx]["label"] = q_edit_text
                    st.session_state.questions[idx]["type"] = q_edit_type
                    st.session_state.questions[idx]["choices"] = [c.strip() for c in q_edit_choices.split(",")] if q_edit_choices else None
                    st.session_state.questions[idx]["skip"] = q_edit_skip
                    st.success("Pertanyaan diupdate!")
                    st.experimental_rerun()

    # Generate XLSForm
    if st.button("Generate & Download XLSForm"):
        survey_dict = {"title": "Survey Streamlit Ultimate", "questions": []}
        choices_master = {}
        
        for q in st.session_state.questions:
            if q["type"] in ["select_one", "select_multiple"]:
                choice_name = f"{q['name']}_choices"
                choices_master[choice_name] = [{"name": c, "label": c} for c in q["choices"]]
                survey_dict["questions"].append({
                    "type": f"{q['type']} {choice_name}",
                    "name": q["name"],
                    "label": q["label"],
                    "relevant": q["skip"] if q["skip"] else None
                })
            else:
                survey_dict["questions"].append({
                    "type": q["type"],
                    "name": q["name"],
                    "label": q["label"],
                    "relevant": q["skip"] if q["skip"] else None
                })

        survey = create_survey_from_dict(survey_dict, choices_dict=choices_master if choices_master else None)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        survey.to_xlsx(temp_file.name)

        st.download_button(
            label="Download XLSForm",
            data=open(temp_file.name, "rb").read(),
            file_name="my_survey.xlsx"
        )
else:
    st.info("Tambahkan pertanyaan menggunakan sidebar untuk mulai membuat form.")
