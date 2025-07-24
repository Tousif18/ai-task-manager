import streamlit as st
import pandas as pd
import joblib
from datetime import datetime

# Load model and task data
priority_model = joblib.load("priority_model.pkl")
task_data = pd.read_csv("tasks_data.csv")

employees = ['Emp_A', 'Emp_B', 'Emp_C']

st.title("🧠 AI-Powered Task Management System")

# Sidebar Navigation
page = st.sidebar.radio("📂 Navigate", ["🔍 Predict Task", "📊 Dashboard"])

if page == "🔍 Predict Task":
    st.header("🔮 Predict Task Priority and Assign Employee")

    with st.form("task_form"):
        task_name = st.text_input("Task Name", placeholder="e.g. Fix login bug")
        estimated_time = st.slider("Estimated Time (in minutes)", 15, 480, 60)
        task_type = st.selectbox("Task Type", task_data['Task_Type'].unique())
        urgency = st.slider("Urgency Score", 1, 10, 5)
        deadline = st.date_input("Deadline", min_value=datetime.today())
        submitted = st.form_submit_button("📌 Predict & Assign")

    if submitted:
        task_length = len(task_name.split())
        days_left = (deadline - datetime.today().date()).days
        task_type_encoded = task_data['Task_Type'].astype('category').cat.categories.get_loc(task_type)

        X_input = pd.DataFrame([[task_length, estimated_time, urgency, days_left, task_type_encoded]],
                               columns=['Task_Length', 'Estimated_Time_Minutes', 'Urgency_Score', 'Days_Left', 'Task_Type_Encoded'])

        predicted_priority = priority_model.predict(X_input)[0]
        st.success(f"✅ Predicted Priority: **{predicted_priority}**")

        workload = task_data['Assigned_Employee'].value_counts().to_dict()
        workload = {emp: workload.get(emp, 0) for emp in employees}
        assigned_employee = min(workload, key=workload.get)

        st.info(f"👤 Assigned to: **{assigned_employee}**")

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
