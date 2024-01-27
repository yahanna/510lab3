import streamlit as st
import sqlite3
import pandas as pd

def create_table():
    conn = sqlite3.connect('todo_database.db')
    cursor = conn.cursor()

    create_table_query = """
    CREATE TABLE IF NOT EXISTS Todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        state TEXT CHECK(state IN ('planned', 'in-progress', 'done')) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT,
        category TEXT CHECK(category IN ('school', 'work', 'life', 'other'))
    );
    """
    cursor.execute(create_table_query)

    conn.commit()

    conn.close()
    
# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('todo_database.db')
    conn.row_factory = sqlite3.Row
    return conn

# 插入新的todo事项
def insert_todo_item(name, description, state='planned', category='other'):
    conn = get_db_connection()
    conn.execute('INSERT INTO Todos (name, description, state, category) VALUES (?, ?, ?, ?)',
                 (name, description, state, category))
    conn.commit()
    conn.close()

# 更新todo事项状态
def update_todo_state(todo_id, new_state):
    conn = get_db_connection()
    conn.execute('UPDATE Todos SET state = ? WHERE id = ?', (new_state, todo_id))
    conn.commit()
    conn.close()

# 获取所有todo事项
def get_all_todos():
    conn = get_db_connection()
    todos = conn.execute('SELECT * FROM Todos').fetchall()
    conn.close()
    return todos

# 获取所有待办事项的函数，现在支持按名称搜索和按类别过滤
def get_filtered_todos(search_query='', category_filter='All'):
    conn = get_db_connection()
    query = 'SELECT * FROM Todos'
    params = []

    if search_query and category_filter != 'All':
        query += ' WHERE name LIKE ? AND category = ?'
        params.extend(['%' + search_query + '%', category_filter])
    elif search_query:
        query += ' WHERE name LIKE ?'
        params.append('%' + search_query + '%')
    elif category_filter != 'All':
        query += ' WHERE category = ?'
        params.append(category_filter)

    todos = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return todos

# 删除待办事项的函数
def delete_todo_item(todo_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM Todos WHERE id = ?', (todo_id,))
    conn.commit()
    conn.close()

# 切换待办事项完成状态的函数
def toggle_todo_completed(todo_id, new_state):
    conn = get_db_connection()
    conn.execute('UPDATE Todos SET state = ? WHERE id = ?', (new_state, todo_id))
    conn.commit()
    conn.close()

## Streamlit界面

def main():
    create_table()
    st.title('Todo List')

    # 添加搜索栏和过滤下拉菜单
    search_query = st.text_input('Search')
    category_filter = st.selectbox('Filter by category', ['All', 'school', 'work', 'life', 'other'])

    # 添加新的待办事项表单
    with st.form(key='add_todo'):
        name = st.text_input('Name')
        description = st.text_area('Description')
        category = st.selectbox('Category', ['school', 'work', 'life', 'other'], index=3)
        submit_button = st.form_submit_button(label='Add Task')
        if submit_button:
            insert_todo_item(name, description, category=category)
            st.success('Task added!')

    # 显示待办事项列表
    st.header('Tasks')

    # 表格标题
    col1, col2, col3, col4, col5 = st.columns([0.1, 2, 4, 2, 2])
    with col1:
        st.write("")  # 这是复选框所在的列
    with col2:
        st.write("Name")
    with col3:
        st.write("Description")
    with col4:
        st.write("Category")
    with col5:
        st.write("State")

    todos_df = get_filtered_todos(search_query, category_filter)

     # 如果DataFrame不为空，则创建自定义的表格布局
    if not todos_df.empty:
        for index, row in todos_df.iterrows():
            # 使用Streamlit的列来创建表格的每一行
            col1, col2, col3, col4, col5, col6 = st.columns([0.5, 2, 2, 2, 2, 0.1])
            with col1:
                # Checkbox for marking the task as done or planned
                completed = st.checkbox("", key=f"complete_{row['id']}", value=row['state'] == 'done')
                if completed != (row['state'] == 'done'):
                    new_state = 'done' if completed else 'planned'
                    update_todo_state(row['id'], new_state)
            with col2:
                st.text(row['name'])
            with col3:
                st.text(row['description'])
            with col4:
                st.text(row['category'])
            with col5:
                # Use colored labels to indicate the task's completion status
                state_text = "completed" if row['state'] == 'done' else "planned"
                state_color = "green" if row['state'] == 'done' else "red"
                st.markdown(f"<span style='color: white; background-color: {state_color}; border-radius: 8px; padding: 3px 6px;'>{state_text}</span>", unsafe_allow_html=True)
            with col6:
                # Delete button
                if st.button("❌", key=f"delete_{row['id']}"):
                    delete_todo_item(row['id'])
                    st.experimental_rerun()  # Rerun the app to update the display

            # Separator line
            st.markdown("---")
    else:
        st.write("No tasks to show.")

if __name__ == '__main__':
    main()
