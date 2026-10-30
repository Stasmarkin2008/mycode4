import imaplib, smtplib                      # Импортируем библиотеки для работы с IMAP и SMTP протоколами
from email.message import EmailMessage        # Импортируем класс для удобного создания письма
from email import message_from_bytes       # Импортируем функцию для преобразования байтов в объект письма
from email.header import decode_header, make_header

def decode_subject(raw):                     #  MIME-тему в читаемый текст
    if not raw:                              # Если темы нет
        return "(без темы)"                  # Возвращаем заглушку
    return str(make_header(decode_header(raw)))  # Склеиваем и декодируем закодированные куски темы

login = input("login: ")                      # Запрашиваем и сохраняем почту (логин)
password = input("password: ")                # Запрашиваем и сохраняем пароль приложения
while True:
    print('1 отправка письма, 2 просмотр последнего письма, 0 выход')
    de=int(input())
    if de==1:
        msg = EmailMessage()                          # Создаем пустой объект электронного письма
        msg['From'] = login                           # Указываем отправителя письма (ваш логин)
        msg['To'] = input("email_to: ")               # Запрашиваем получателя и записываем в поле «Кому»
        msg['Subject'] = "Консольный клиент Gmail"    # Устанавливаем фиксированную тему письма
        msg.set_content(input("body: "))              # Запрашиваем текст и записываем в тело письма

        if path := input("ask if attach file by path (путь или Enter): "):  # Запрашиваем путь к файлу и проверяем, введено ли что-то
            with open(path, 'rb') as f:               # Открываем файл в бинарном режиме для чтения
                msg.add_attachment(                   # Прикрепляем файл к письму:
                    f.read(),                         # -- считываем содержимое файла в байтах
                    maintype='application',           # -- задаем основной тип данных
                    subtype='octet-stream',           # -- задаем подтип данных (бинарный поток)
                    filename=path.split('/')[-2]      # -- извлекаем только имя файла из пути
                )

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:  # Безопасно подключаемся к SMTP-серверу Gmail по порту 465
            s.login(login, password)                  # Авторизуемся на SMTP-сервере под вашим аккаунтом
            s.send_message(msg)                       # Отправляем готовое сообщение
        print("Отправлено!")                          # Выводим сообщение об успешной отправке

    elif de==2:
        with imaplib.IMAP4_SSL('imap.gmail.com') as m:  # Безопасно подключаемся к IMAP-серверу Gmail
            m.login(login, password)                  # Авторизуемся в почтовом ящике через IMAP
            m.select('inbox')                         # Выбираем папку «Входящие» для работы
            _, data = m.search(None, 'ALL')           # Ищем все письма в выбранной папке
            if ids := data[0].split():                # Получаем список ID писем и проверяем, есть ли они
                ids = ids[-30:]                       
                letters = []                          # Список пар (id, тема)
                print("--- Список тем ---")           # Заголовок списка тем
                for mail_id in ids:                   # Перебираем все ID писем
                    _, hdr = m.fetch(mail_id, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')  # Забираем только тему (не помечая прочитанным)
                    subj = decode_subject(message_from_bytes(hdr[0][1])['Subject'])    # Декодируем тему
                    letters.append((mail_id, subj))   # Сохраняем ID и тему
                    print(f"Тема: {subj}")            # Выводим тему на экран

                choice = input("Введите тему письма: ").strip()  # Спрашиваем у пользователя тему
                found = [l for l in letters if choice.lower() in l[1].lower()]  # Ищем письма, где тема содержит введённый текст
                if not found:                         # Если ничего не нашли
                    print("Письмо с такой темой не найдено.")  # Сообщаем об этом
                    exit()                            # И выходим
                mail_id = found[0][0]                 # Берём ID первого найденного письма

                _, mail_data = m.fetch(mail_id, '(RFC822)')  # Скачиваем найденное письмо по его ID
                parsed_msg = message_from_bytes(mail_data[0][1])  # Превращаем байты скачанного письма в объект
                
                print("--- Последнее письмо в ящике ---")  # Выводим заголовок для блока просмотра
                print(f"От: {parsed_msg['From']}")          # Выводим отправителя письма
                print(f"Тема: {decode_subject(parsed_msg['Subject'])}")  # Декодируем и выводим тему письма
                
                if parsed_msg.is_multipart():         # Проверяем, состоит ли письмо из нескольких частей (например, текст + файл)
                    for part in parsed_msg.walk():    # Перебираем все части письма по очереди
                        if part.get_content_type() == "text/plain":  # Ищем ту часть, где находится обычный текст
                            print(f"Содержание: {part.get_payload(decode=True).decode(errors='ignore')}")  # Выводим текст
                            break                     # Прерываем цикл после нахождения текстовой части
                    for part in parsed_msg.walk():    # Ещё раз перебираем части письма
                        filename = part.get_filename()  # Получаем имя файла (None, если это не вложение)
                        if filename:                    # Если у части есть имя файла — это вложение
                            filename = decode_subject(filename)  # Декодируем имя (кириллица в заголовках)
                            payload = part.get_payload(decode=True)  # Декодируем содержимое файла
                            if payload:                 # Если содержимое не пустое
                                with open(filename, 'wb') as f:  # Открываем файл на запись в бинарном режиме
                                    f.write(payload)    # Записываем байты в файл
                                print(f"Вложение сохранено: {filename}")  # Сообщаем, куда сохранили
                    # --- КОНЕЦ ДОБАВЛЕННОГО БЛОКА ---
                else:
                    print(f"Содержание: {parsed_msg.get_payload(decode=True).decode(errors='ignore')}")  # Выводим текст для простого письма
    elif de==0:
        break