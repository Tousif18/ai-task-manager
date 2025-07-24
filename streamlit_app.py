import streamlit as st
import pandas as pd
import joblib
from datetime import datetime
def recommend_task_type(task_name):
    task_name = task_name.lower()

    keyword_map = {
        "analysis": ["analyze", "analysis", "assess", "evaluate"],
        "design": ["design", "mockup", "layout", "wireframe"],
        "development": ["build", "develop", "code", "implement"],
        "testing": ["test", "debug", "qa", "verify"],
        "research": ["research", "study", "explore", "read"],
        "documentation": ["write", "doc", "document", "manual"],
    }

    for task_type, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword in task_name:
                return task_type.capitalize()

    return "Analysis"  # fallback

# Load the original task type options from the template file
template_df = pd.read_csv("tasks_data.csv")

# Load model and task data
priority_model = joblib.load("priority_model.pkl")
import os

if os.path.exists("task_log.csv"):
    task_data = pd.read_csv("task_log.csv")
else:
    # fallback if no user logs yet
    task_data = pd.read_csv("tasks_data.csv")


# Optional: set app metadata (optional but good UX)
st.set_page_config(page_title="AI Task Manager", layout="centered")

# 👥 Dynamic Employee Management in Sidebar
st.sidebar.header("👥 Employee Management")

default_employees = ["Emp_A", "Emp_B", "Emp_C"]
custom_employees = st.sidebar.text_area(
    "Enter employee names (comma-separated)", 
    value=", ".join(default_employees)
)

# Final employee list used across the app
employees = [e.strip() for e in custom_employees.split(",") if e.strip()]

# App title
st.title("🧠 AI-Powered Task Management System")


# Sidebar Navigation
page = st.sidebar.radio("📂 Navigate", ["🔍 Predict Task", "📊 Dashboard"])

if page == "🔍 Predict Task":
    st.header("🔮 Predict Task Priority and Assign Employee")

    with st.form("task_form"):
        task_name = st.text_input("Task Name", placeholder="e.g. Fix login bug")
        if task_name.strip():
            suggested_type = recommend_task_type(task_name)
            st.caption(f"💡 Suggested Task Type: **{suggested_type}**")
        else:
            suggested_type = "Analysis"

        estimated_time = st.slider("Estimated Time (in minutes)", 15, 480, 60)
        task_type = st.selectbox(
             "Task Type", 
              template_df['Task_Type'].unique(), 
              index=list(template_df['Task_Type'].unique()).index(suggested_type) 
              if suggested_type in template_df['Task_Type'].unique() else 0
        )

        urgency = st.slider("Urgency Score", 1, 10, 5)
        deadline = st.date_input("Deadline", min_value=datetime.today())
        submitted = st.form_submit_button("📌 Predict & Assign")

    if submitted:
        task_length = len(task_name.split())
        days_left = (deadline - datetime.today().date()).days
        # Encode task type safely using template_df (always has all types)
        all_types = template_df['Task_Type'].astype('category').cat.categories
        if task_type in all_types:
          task_type_encoded = all_types.get_loc(task_type)
        else:
          task_type_encoded = 0  # fallback to first type


        X_input = pd.DataFrame([[task_length, estimated_time, urgency, days_left, task_type_encoded]],
                               columns=['Task_Length', 'Estimated_Time_Minutes', 'Urgency_Score', 'Days_Left', 'Task_Type_Encoded'])

        predicted_priority = priority_model.predict(X_input)[0]
        confidence = priority_model.predict_proba(X_input).max()
        
        st.success(f"✅ Predicted Priority: **{predicted_priority}**")
        st.caption(f"🤖 Model confidence: {confidence:.2%}")
        workload = task_data['Assigned_Employee'].value_counts().to_dict()
        workload = {emp: workload.get(emp, 0) for emp in employees}
        assigned_employee = min(workload, key=workload.get)

        st.info(f"👤 Assigned to: **{assigned_employee}**")
        new_task = {
            'Task_Name': task_name,
            'Estimated_Time_Minutes': estimated_time,
            'Urgency_Score': urgency,
            'Days_Left': days_left,
            'Task_Type': task_type,
            'Priority': predicted_priority,
            'Assigned_Employee': assigned_employee
        }

        # Convert to DataFrame and append to CSV
        new_df = pd.DataFrame([new_task])
        if os.path.exists("task_log.csv"):
           new_df.to_csv("task_log.csv", mode='a', header=False, index=False)
        else:
           new_df.to_csv("task_log.csv", index=False)

elif page == "📊 Dashboard":
    st.header("📊 Task Assignment Dashboard")

    st.subheader("📌 Tasks per Employee")
    st.bar_chart(task_data['Assigned_Employee'].value_counts())

    st.subheader("📈 Priority Distribution")
    st.bar_chart(task_data['Priority'].value_counts())

    st.subheader("🧪 Urgency vs Priority Score")
    if 'Urgency_Score' in task_data.columns and 'Priority_Score' in task_data.columns:
        st.scatter_chart(task_data[['Urgency_Score', 'Priority_Score']])
    else:
        st.warning("Priority_Score not available for scatter plot.")
    st.subheader("⬇️ Export Assigned Tasks")
    st.download_button(
       label="Download as CSV",
       data=task_data.to_csv(index=False),
       file_name='assigned_tasks.csv',
       mime='text/csv'
    )
