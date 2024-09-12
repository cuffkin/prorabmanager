import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_tags import st_tags

# Функция для загрузки данных из файла
def load_data(file_path, columns=None):
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        return pd.DataFrame(columns=columns)

# Загрузка данных для стоимости доставок
data_file_delivery = os.path.join(os.path.dirname(__file__), 'logisticpricebase.xlsx')
df_delivery = load_data(data_file_delivery, columns=['Название зоны', 'ID зоны', 'Название улиц в зоне',
                                                     'Стоимость доставки ГАЗель', 'Стоимость доставки Валдай/ ГАЗон, ЗиЛ',
                                                     'Стоимость доставки КАМаз', 'Ср. расстояние от базы (км)'])

# Исправление названия столбца
df_delivery.columns = df_delivery.columns.str.replace('\n', ' ')

# Загрузка данных для долгов клиентов
data_file_debts = os.path.join(os.path.dirname(__file__), 'debtbase.xlsx')
df_debts = load_data(data_file_debts, columns=['Клиент', 'Организация', 'Сумма долга', 'Номер документа', 'Срок оплаты', 'Выдавший долг'])

# Загрузка данных для истории операций
data_file_history = os.path.join(os.path.dirname(__file__), 'historybase.xlsx')
df_history = load_data(data_file_history, columns=['Клиент', 'Организация', 'Операция', 'Сумма', 'Дата операции', 'Кто выполнил операцию', 'Примечания'])

# Загрузка данных для заказов и водителей
data_file_orders = os.path.join(os.path.dirname(__file__), 'orders.xlsx')
df_orders = load_data(data_file_orders, columns=['Номер заказа', 'Время добавления', 'Статус', 'Имя водителя', 'Кто закрыл заказ', 'Выполненные заказы'])

# Загрузка данных для машин
data_file_trucks = os.path.join(os.path.dirname(__file__), 'drivers.xlsx')
df_trucks = load_data(data_file_trucks, columns=['Имя водителя', 'Макс. грузоподъемность', 'Боковая выгрузка', 'Статус авто', 'Выполненные заказы (номера)'])

# Функция для получения уникальных значений из столбца
def get_unique_values(column_name, df):
    return df[column_name].dropna().unique().tolist()

# Функция для добавления записи в историю
def add_to_history(client, organization, operation, amount, operation_date, performed_by, notes):
    global df_history
    new_history_entry = {
        'Клиент': client,
        'Организация': organization,
        'Операция': operation,
        'Сумма': amount,
        'Дата операции': operation_date,
        'Кто выполнил операцию': performed_by,
        'Примечания': notes
    }
    df_history = pd.concat([df_history, pd.DataFrame([new_history_entry])], ignore_index=True)
    df_history.to_excel(data_file_history, index=False)

# Подсветка просроченных долгов
def highlight_overdue(row):
    if 'Срок оплаты' in row.index and pd.notna(row['Срок оплаты']) and row['Срок оплаты'] < pd.Timestamp(datetime.now().date()) and row['Сумма долга'] > 0:
        return ['background-color: red'] * len(row)
    return [''] * len(row)

# Подсветка статусов заказов и машин
def highlight_status(status):
    if status == "Свободен":
        return 'background-color: yellow'
    elif status == "В пути" or status == "Занят":
        return 'background-color: orange'
    elif status == "На ремонте":
        return 'background-color: green'
    return ''

# Основное меню для выбора страницы
menu = ["Управление доставками", "Управление долгами", "История операций", "Менеджер заказов"]
choice = st.sidebar.selectbox("Выберите страницу", menu)

# Страница управления доставками
if choice == "Управление доставками":
    st.title("Управление доставками")

    tabs = st.tabs(["Поиск", "Добавление зоны", "Редактирование зон", "Список зон"])

    # Вкладка поиска зон доставки
    with tabs[0]:
        st.header("Поиск зон доставки")

        options = get_unique_values('Название улиц в зоне', df_delivery) + get_unique_values('Название зоны', df_delivery)
        query = st_tags(
            label='Введите адрес или зону',
            text='Press enter to add more',
            value='',
            suggestions=options,
            maxtags=1,
            key='search_zone'
        )

        if query:
            query = query[0]
            matching_results = df_delivery[df_delivery.apply(lambda row: query.lower() in str(row).lower(), axis=1)]
            if not matching_results.empty:
                st.dataframe(matching_results, use_container_width=True)

                selected_index = st.selectbox("Выберите строку для отображения деталей", matching_results.index)
                selected_row = matching_results.loc[selected_index]
                st.markdown(f"**Зона:** {selected_row['Название зоны']}")
                st.markdown(f"**ID зоны:** {selected_row['ID зоны']}")
                st.markdown(f"<b>ГАЗель:</b> {selected_row['Стоимость доставки ГАЗель']}", unsafe_allow_html=True)
                st.markdown(f"<b>Валдай/ ГАЗон, ЗиЛ:</b> {selected_row['Стоимость доставки Валдай/ ГАЗон, ЗиЛ']}", unsafe_allow_html=True)
                st.markdown(f"<b>КАМаз:</b> {selected_row['Стоимость доставки КАМаз']}", unsafe_allow_html=True)
                st.markdown(f"**Расстояние от базы:** {selected_row['Ср. расстояние от базы (км)']} км")

    # Вкладка добавления новой зоны
    with tabs[1]:
        st.header("Добавление новой зоны")

        zone_name = st.text_input("Название зоны", "")
        zone_id = st.text_input("ID зоны", "")
        streets = st.text_input("Название улиц в зоне", "")

        col1, col2, col3 = st.columns(3)
        with col1:
            gazel_cost = st.number_input("ГАЗель", key="gazel_cost")
        with col2:
            valday_cost = st.number_input("Валдай/ ГАЗон, ЗиЛ", key="valday_cost")
        with col3:
            kamaz_cost = st.number_input("КАМаз", key="kamaz_cost")

        distance = st.number_input("Ср. расстояние от базы (км)", key="distance")

        if st.button("Добавить зону"):
            new_data = {
                "Название зоны": zone_name,
                "ID зоны": zone_id,
                "Название улиц в зоне": streets,
                "Стоимость доставки ГАЗель": gazel_cost,
                "Стоимость доставки Валдай/ ГАЗон, ЗиЛ": valday_cost,
                "Стоимость доставки КАМаз": kamaz_cost,
                "Ср. расстояние от базы (км)": distance
            }
            df_delivery = pd.concat([df_delivery, pd.DataFrame([new_data])], ignore_index=True)
            df_delivery.to_excel(data_file_delivery, index=False)
            st.rerun()  # Перезапуск приложения после добавления новой зоны

    # Вкладка редактирования зон
    with tabs[2]:
        st.header("Редактирование зон")
        selected_zone = st.selectbox("Выберите зону для редактирования", df_delivery['Название зоны'].unique(), key="edit_zone")
        
        if selected_zone:
            zone_data = df_delivery[df_delivery['Название зоны'] == selected_zone].iloc[0]
            
            zone_name_edit = st.text_input("Название зоны", value=zone_data['Название зоны'], key="zone_name_edit")
            zone_id_edit = st.text_input("ID зоны", value=zone_data['ID зоны'], key="zone_id_edit")
            streets_edit = st.text_input("Название улиц в зоне", value=zone_data['Название улиц в зоне'], key="streets_edit")

            col1, col2, col3 = st.columns(3)
            with col1:
                gazel_cost_edit = st.number_input("ГАЗель", value=zone_data['Стоимость доставки ГАЗель'], key="gazel_cost_edit")
            with col2:
                valday_cost_edit = st.number_input("Валдай/ ГАЗон, ЗиЛ", value=zone_data['Стоимость доставки Валдай/ ГАЗон, ЗиЛ'], key="valday_cost_edit")
            with col3:
                kamaz_cost_edit = st.number_input("КАМаз", value=zone_data['Стоимость доставки КАМаз'], key="kamaz_cost_edit")
            distance_edit = st.number_input("Ср. расстояние от базы (км)", value=zone_data['Ср. расстояние от базы (км)'], key="distance_edit")

            if st.button("Сохранить изменения"):
                df_delivery.loc[df_delivery['Название зоны'] == selected_zone, :] = [zone_name_edit, zone_id_edit, streets_edit, gazel_cost_edit, valday_cost_edit, kamaz_cost_edit, distance_edit]
                df_delivery.to_excel(data_file_delivery, index=False)
                st.success("Данные успешно обновлены!")
                st.rerun()

        st.header("Удаление зоны")
        selected_zone_del = st.selectbox("Выберите зону для удаления", df_delivery['Название зоны'].unique(), key="del_zone")
        if st.button("Удалить зону"):
            df_delivery = df_delivery[df_delivery['Название зоны'] != selected_zone_del]
            df_delivery.to_excel(data_file_delivery, index=False)
            st.success(f"Зона '{selected_zone_del}' успешно удалена!")
            st.rerun()

    # Вкладка списка зон
    with tabs[3]:
        st.header("Список зон доставки")
        st.dataframe(df_delivery, use_container_width=True)

# Страница управления долгами
elif choice == "Управление долгами":
    st.title("Управление долгами клиентов")

    debt_tabs = st.tabs(["Список должников", "Добавить новый долг", "Редактировать долг"])

    # Вкладка "Список должников"
    with debt_tabs[0]:
        st.header("Список должников")
        st.dataframe(df_debts[['Клиент', 'Организация', 'Сумма долга']].style.apply(highlight_overdue, axis=1), use_container_width=True)

        # Просмотр долгов по клиенту в разрезе
        for client in df_debts['Клиент'].unique():
            with st.expander(f"Долги по клиенту: {client}"):
                client_debts = df_debts[df_debts['Клиент'] == client]
                st.dataframe(client_debts[['Номер документа', 'Сумма долга', 'Срок оплаты', 'Выдавший долг']].style.apply(highlight_overdue, axis=1), use_container_width=True)

    # Вкладка "Добавить новый долг"
    with debt_tabs[1]:
        st.header("Добавить новый долг")
        existing_client = st.selectbox("Выберите существующего клиента", ["Добавить нового"] + df_debts['Клиент'].tolist(), key="existing_client")

        if existing_client == "Добавить нового":
            new_client = st.text_input("Имя нового клиента", key="new_client")
            new_org = st.text_input("Название организации", key="new_org")
        else:
            new_client = existing_client
            new_org = df_debts[df_debts['Клиент'] == existing_client]['Организация'].values[0]

        new_debt_amount = st.number_input("Сумма долга", min_value=0.0, key="new_debt_amount")
        new_doc_number = st.text_input("Номер документа", key="new_doc_number")
        new_due_date = st.date_input("Срок оплаты", key="new_due_date")
        new_issuer = st.text_input("Кто выдал долг", key="new_issuer")

        if st.button("Добавить долг"):
            new_debt_data = {
                'Клиент': new_client,
                'Организация': new_org,
                'Сумма долга': new_debt_amount,
                'Номер документа': new_doc_number,
                'Срок оплаты': new_due_date,
                'Выдавший долг': new_issuer
            }

            # Если клиент новый, добавляем его в DataFrame
            df_debts = pd.concat([df_debts, pd.DataFrame([new_debt_data])], ignore_index=True)

            # Запись в историю
            add_to_history(new_client, new_org, "Добавление долга", new_debt_amount, new_due_date, new_issuer, new_doc_number)
            st.rerun()  # Перезапуск приложения после добавления нового долга

    # Вкладка "Редактировать долг"
    with debt_tabs[2]:
        st.header("Редактировать долг")
        selected_debtor = st.selectbox("Выберите должника", df_debts['Клиент'].unique(), key="selected_debtor")
        
        if selected_debtor:
            debtor_data = df_debts[df_debts['Клиент'] == selected_debtor]
            st.write(debtor_data)

            reduce_amount = st.number_input("Сумма для частичного погашения", min_value=0.0, max_value=float(debtor_data['Сумма долга'].values[0]), key="reduce_amount")
            close_debt = st.checkbox("Закрыть долг полностью?", key="close_debt")

            if close_debt:
                reduce_amount = debtor_data['Сумма долга'].values[0]

            close_date = st.date_input("Дата закрытия", key="close_date")
            closed_by = st.text_input("Кто закрыл", key="closed_by")
            note = st.text_input("Примечания", key="note")
            pko_number = st.text_input("Номер ПКО", key="pko_number")

            if (note or pko_number) and st.button("Обновить долг"):
                # Обновление суммы долга
                df_debts.loc[df_debts['Клиент'] == selected_debtor, 'Сумма долга'] -= reduce_amount

                # Запись в историю
                add_to_history(selected_debtor, debtor_data['Организация'].values[0], "Погашение долга", reduce_amount, close_date, closed_by, pko_number or note)

                # Если долг полностью закрыт
                if df_debts.loc[df_debts['Клиент'] == selected_debтор, 'Сумма долга'].values[0] == 0:
                    df_debts.drop(df_debts[df_deбts['Клиент'] == selected_deбтор].index, inplace=True)

                df_debts.to_excel(data_file_debts, index=False)
                st.rerun()  # Перезапуск приложения после обновления долга

# Страница истории операций
elif choice == "История операций":
    st.title("История операций")

    # Отображение истории операций
    st.dataframe(df_history, use_container_width=True)

# Страница менеджера заказов
elif choice == "Менеджер заказов":
    st.title("Менеджер заказов доставки")

    order_tabs = st.tabs(["Список заказов", "Добавить новый заказ", "Редактировать заказ", "Машины"])

    # Вкладка "Список заказов"
    with order_tabs[0]:
        st.header("Список заказов")
        st.dataframe(df_orders.style.applymap(lambda x: highlight_status(x), subset=['Статус']))

        selected_order_index = st.selectbox("Выберите заказ для удаления", df_orders.index, format_func=lambda x: df_orders.loc[x, "Номер заказа"])

        if selected_order_index is not None:
            selected_order = df_orders.loc[selected_order_index]

            st.markdown(f"**Выбранный заказ:** {selected_order['Номер заказа']}")
            st.markdown(f"**Статус:** {selected_order['Статус']}")
            st.markdown(f"**Водитель:** {selected_order['Имя водителя']}")

            # Кнопка для удаления заказа
            if st.button("Удалить заказ"):
                df_orders = df_orders.drop(selected_order_index)  # Удаляем заказ из DataFrame
                df_orders.to_excel(data_file_orders, index=False)  # Сохраняем изменения в Excel
                st.success(f"Заказ {selected_order['Номер заказа']} успешно удален.")
                st.rerun()  # Перезапуск приложения для обновления данных

    # Вкладка "Добавить новый заказ"
    with order_tabs[1]:
        st.header("Добавить новый заказ")

        # Получаем список водителей из таблицы с машинами
        driver_name = st.selectbox("Выберите водителя", df_trucks['Имя водителя'].unique(), key="driver_name")
        order_number = st.text_input("Номер заказа", key="order_number")
        order_status = st.selectbox("Статус заказа", ["В ожидании", "В пути", "Выполнен", "Отменён"], key="order_status")
        closed_by = st.text_input("Кто закрыл заказ (оператор)", key="closed_by_order")

        if st.button("Добавить заказ"):
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            new_order = {
                'Номер заказа': order_number,
                'Время добавления': current_time,
                'Статус': order_status,
                'Имя водителя': driver_name,
                'Кто закрыл заказ': closed_by,
                'Выполненные заказы': 0  # Изначально ноль, увеличиваем только по факту выполнения
            }
            df_orders = pd.concat([df_orders, pd.DataFrame([new_order])], ignore_index=True)
            df_orders.to_excel(data_file_orders, index=False)
            st.rerun()  # Перезапуск приложения после добавления нового заказа

            # Обновляем статус машины
            df_trucks.loc[df_trucks['Имя водителя'] == driver_name, 'Статус авто'] = order_status
            completed_orders = df_trucks.loc[df_trucks['Имя водителя'] == driver_name, 'Выполненные заказы (номера)'].values[0]
            if pd.isna(completed_orders) or completed_orders == "":
                completed_orders = str(order_number)
            else:
                completed_orders = str(completed_orders) + f", {order_number}"
            df_trucks.loc[df_trucks['Имя водителя'] == driver_name, 'Выполненные заказы (номера)'] = completed_orders
            df_trucks.to_excel(data_file_trucks, index=False)

    # Вкладка "Редактировать заказ"
    with order_tabs[2]:
        st.header("Редактировать заказ")
        selected_order = st.selectbox("Выберите заказ", df_orders['Номер заказа'].unique(), key="selected_order")

        if not selected_order:
            st.warning("Выберите заказ для редактирования.")
        else:
            order_data = df_orders[df_orders['Номер заказа'] == selected_order]

            if not order_data.empty:
                current_status = order_data['Статус'].values[0]
                try:
                    status_index = ["В ожидании", "В пути", "Выполнен", "Отменён"].index(current_status)
                except ValueError:
                    status_index = 0

                new_status = st.selectbox(
                    "Изменить статус", 
                    ["В ожидании", "В пути", "Выполнен", "Отменён"],
                    index=status_index,
                    key="new_status"
                )

                if st.button("Обновить статус заказа"):
                    df_orders.loc[df_orders['Номер заказа'] == selected_order, 'Статус'] = new_status

                    if new_status == "Выполнен":
                        df_orders.loc[df_orders['Номер заказа'] == selected_order, 'Выполненные заказы'] += 1

                    # Обновляем статус машины
                    driver_name = df_orders.loc[df_orders['Номер заказа'] == selected_order, 'Имя водителя'].values[0]
                    df_trucks.loc[df_trucks['Имя водителя'] == driver_name, 'Статус авто'] = new_status

                    completed_orders = df_trucks.loc[df_trucks['Имя водителя'] == driver_name, 'Выполненные заказы (номера)'].values[0]
                    if pd.isna(completed_orders) or completed_orders == "":
                        completed_orders = str(selected_order)
                    else:
                        completed_orders = str(completed_orders) + f", {selected_order}"
                    df_trucks.loc[df_trucks['Имя водителя'] == driver_name, 'Выполненные заказы (номера)'] = completed_orders

                    df_orders.to_excel(data_file_orders, index=False)
                    df_trucks.to_excel(data_file_trucks, index=False)
                    st.rerun()  # Перезапуск приложения после обновления заказа

    # Вкладка "Машины"
    with order_tabs[3]:
        st.header("Список машин и их текущий статус")

        def can_change_status(driver_name):
            active_orders = df_orders[(df_orders['Имя водителя'] == driver_name) & (df_orders['Статус'].isin(["В ожидании", "В пути"]))] 
            return active_orders.empty

        for index, row in df_trucks.iterrows():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"<div style='font-size: 18px;'><strong>Водитель: {row['Имя водителя']}</strong></div>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"<div style='font-size: 16px; {highlight_status(row['Статус авто'])}'>Текущий статус: {row['Статус авто']}</div>",
                    unsafe_allow_html=True
                )
            with col2:
                if can_change_status(row['Имя водителя']):
                    try:
                        status_index = ["Свободен", "В пути", "На ремонте", "Занят"].index(row['Статус авто'])
                    except ValueError:
                        status_index = 0

                    new_status = st.selectbox(
                        "Изменить статус",
                        ["Свободен", "В пути", "На ремонте", "Занят"],
                        index=status_index,
                        key=f"status_{index}"
                    )
                    if st.button(f"✔", key=f"save_status_{index}"):
                        df_trucks.at[index, 'Статус авто'] = new_status
                        df_trucks.to_excel(data_file_trucks, index=False)
                        st.rerun()  # Перезапуск приложения после изменения статуса машины
                        st.success(f"Статус для {row['Имя водителя']} обновлен")
                else:
                    st.warning(f"Статус для {row['Имя водителя']} нельзя изменить, т.к. есть активные заказы")

        st.header("Редактирование или удаление водителя")

        # Выбор водителя для редактирования или удаления
        selected_driver = st.selectbox("Выберите водителя для редактирования или удаления", df_trucks['Имя водителя'].unique(), key="selected_driver")

        if selected_driver:
            driver_data = df_trucks[df_trucks['Имя водителя'] == selected_driver].iloc[0]

            # Поля для редактирования информации о водителе
            new_driver_name = st.text_input("Имя водителя", value=driver_data['Имя водителя'], key="edit_driver_name")
            new_capacity = st.number_input("Макс. грузоподъемность (тонн)", value=driver_data['Макс. грузоподъемность'], key="edit_capacity")
            new_side_unloading = st.selectbox("Боковая выгрузка", ["Да", "Нет"], index=0 if driver_data['Боковая выгрузка'] == "Да" else 1, key="edit_side_unloading")
            new_status = st.selectbox("Статус авто", ["Свободен", "В пути", "На ремонте", "Занят"], key="edit_status")

            # Кнопка для сохранения изменений водителя
            if st.button("Сохранить изменения водителя"):
                df_trucks.loc[df_trucks['Имя водителя'] == selected_driver, :] = [new_driver_name, new_capacity, new_side_unloading, new_status, driver_data['Выполненные заказы (номера)']]
                df_trucks.to_excel(data_file_trucks, index=False)
                st.success(f"Информация о водителе {selected_driver} успешно обновлена!")
                st.rerun()

            # Кнопка для удаления водителя
            if st.button("Удалить водителя"):
                df_trucks = df_trucks[df_trucks['Имя водителя'] != selected_driver]
                df_trucks.to_excel(data_file_trucks, index=False)
                st.success(f"Водитель {selected_driver} успешно удалён!")
                st.rerun()

        st.header("Добавить новую машину")
        
        new_driver_name = st.text_input("Имя водителя", key="new_driver_name")
        max_capacity = st.number_input("Макс. грузоподъемность (тонн)", min_value=0.0, key="new_capacity")
        side_unloading = st.selectbox("Боковая выгрузка", ["Да", "Нет"], key="new_side_unloading")
        initial_status = st.selectbox("Начальный статус", ["Свободен", "В пути", "На ремонте", "Занят"], key="new_initial_status")

        if st.button("Добавить машину"):
            new_truck = {
                'Имя водителя': new_driver_name,
                'Макс. грузоподъемность': max_capacity,
                'Боковая выгрузка': side_unloading,
                'Статус авто': initial_status,
                'Выполненные заказы (номера)': ''
            }
            df_trucks = pd.concat([df_trucks, pd.DataFrame([new_truck])], ignore_index=True)
            df_trucks.to_excel(data_file_trucks, index=False)
            st.rerun()  # Перезапуск приложения после добавления новой машины
            st.success("Новая машина добавлена")