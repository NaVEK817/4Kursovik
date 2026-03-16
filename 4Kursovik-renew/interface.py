import warnings

# В некоторых окружениях warnings могут быть превращены в ошибки (PYTHONWARNINGS=error).
# Это не должно блокировать запуск GUI, поэтому глушим конкретные предупреждения LangChain.
warnings.filterwarnings(
    "ignore",
    message=r"Core Pydantic V1 functionality isn't compatible with Python 3\.14 or greater\.",
    category=UserWarning,
)
warnings.filterwarnings(
    "ignore",
    message=r"The class `Ollama` was deprecated.*",
    category=DeprecationWarning,
)

import json
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from auth import authenticate, create_user, has_any_users
from vacancy_agent import OUTPUT_FILE, LINKS_FILE, VacancyParserAgent
from vacancy_docx import save_vacancy_to_docx


class HRApp(tk.Tk):
    """Графическая оболочка для HR‑агентства S7.

    Возможности:
    - запуск парсера вакансий;
    - просмотр базовой информации по собранным вакансиям;
    - отображение статуса выполнения.
    """

    def __init__(self) -> None:
        super().__init__()
        # Сначала выполняем вход, затем показываем основное окно.
        self.withdraw()
        self.title("S7 HR‑сервис — вакансии")
        self._configure_window()

        self.parser_thread: threading.Thread | None = None
        self.vacancies: list[dict] = []
        self.progress_total: int = 0
        self.progress_done: int = 0
        self.current_user: str | None = None

        # Окно интерфейса пока скрыто — сначала логин/создание пользователя.
        if not self._startup_auth_flow():
            self.destroy()
            return

        # После успешного входа строим и показываем основное окно.
        self._create_widgets()
        self._load_vacancies_from_file(initial=True)
        self._apply_auth_state()
        self.deiconify()

    # ---------- Конфигурация окна ----------
    def _configure_window(self) -> None:
        self.minsize(900, 600)
        try:
            self.iconbitmap(default="")  # безопасный вызов: без иконки на всех платформах
        except Exception:
            pass

        self._center_on_screen()

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        width = self.winfo_width() or 900
        height = self.winfo_height() or 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ---------- Виджеты ----------
    def _create_widgets(self) -> None:
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Верхняя панель с информацией и кнопками
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            top_frame,
            text="HR‑сервис S7 — управление вакансиями",
            font=("Segoe UI", 14, "bold"),
        )
        title_label.pack(side=tk.LEFT)

        buttons_frame = ttk.Frame(top_frame)
        buttons_frame.pack(side=tk.RIGHT)

        # Кнопки управления
        self.compose_button = ttk.Button(
            buttons_frame,
            text="Составить вакансию",
            command=self._on_compose_vacancy_clicked,
        )
        self.compose_button.pack(side=tk.LEFT, padx=(0, 5))

        self.schedule_button = ttk.Button(
            buttons_frame,
            text="Расписание собеседований",
            command=self._on_schedule_clicked,
        )
        self.schedule_button.pack(side=tk.LEFT, padx=(0, 5))

        self.run_button = ttk.Button(
            buttons_frame, text="Запустить парсер", command=self._on_run_parser_clicked
        )
        self.run_button.pack(side=tk.LEFT, padx=(0, 5))

        self.reload_button = ttk.Button(
            buttons_frame, text="Обновить список", command=self._on_reload_clicked
        )
        self.reload_button.pack(side=tk.LEFT)

        self.auth_button = ttk.Button(
            buttons_frame,
            text="Войти",
            command=self._on_auth_button_clicked,
        )
        self.auth_button.pack(side=tk.LEFT, padx=(10, 0))

        # Статусная строка
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 5))

        ttk.Label(status_frame, text="Статус:").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Ожидание действий пользователя")
        self.status_label = ttk.Label(
            status_frame, textvariable=self.status_var, foreground="#007700"
        )
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))

        # Индикатор прогресса парсера (в процентах)
        self.progress_var = tk.StringVar(value="")
        self.progress_label = ttk.Label(
            status_frame, textvariable=self.progress_var, anchor=tk.W
        )
        self.progress_label.pack(side=tk.LEFT, padx=(10, 0))

        self.counter_var = tk.StringVar(value="Вакансий в базе: 0")
        self.counter_label = ttk.Label(
            status_frame, textvariable=self.counter_var, anchor=tk.E
        )
        self.counter_label.pack(side=tk.RIGHT)

        # Таблица с вакансиями
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        columns = ("title", "area", "salary", "responses", "experience", "employment", "schedule")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("title", text="Должность")
        self.tree.heading("area", text="Город")
        self.tree.heading("salary", text="Зарплата")
        self.tree.heading("responses", text="Отклики")
        self.tree.heading("experience", text="Опыт")
        self.tree.heading("employment", text="Занятость")
        self.tree.heading("schedule", text="График")

        self.tree.column("title", width=260, anchor=tk.W)
        self.tree.column("area", width=120, anchor=tk.W)
        self.tree.column("salary", width=130, anchor=tk.W)
        self.tree.column("responses", width=90, anchor=tk.CENTER)
        self.tree.column("experience", width=130, anchor=tk.W)
        self.tree.column("employment", width=120, anchor=tk.W)
        self.tree.column("schedule", width=120, anchor=tk.W)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Открытие подробной информации по вакансии по двойному клику
        self.tree.bind("<Double-1>", self._on_row_double_click)

        # Нижняя панель с подсказкой и путями
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(5, 0))

        links_path = Path(LINKS_FILE).resolve()
        output_path = Path(OUTPUT_FILE).resolve()
        info_text = (
            f"Файл ссылок: {links_path}    "
            f"Файл результатов: {output_path}"
        )
        ttk.Label(
            bottom_frame,
            text=info_text,
            font=("Segoe UI", 8),
            foreground="#555555",
            wraplength=860,
            justify=tk.LEFT,
        ).pack(side=tk.LEFT)

    # ---------- Авторизация ----------
    def _startup_auth_flow(self) -> bool:
        try:
            have_users = has_any_users()
        except Exception:
            have_users = False

        if not have_users:
            ok = self._show_first_user_setup_dialog()
            if not ok:
                # Пользователь отменил создание — остаёмся без авторизации.
                self.current_user = None
                self._apply_auth_state()
                return False

        user = self._show_login_dialog()
        if not user:
            # Пользователь отменил вход.
            self.current_user = None
            self._apply_auth_state()
            return False

        self.current_user = user
        return True

    def _apply_auth_state(self) -> None:
        is_authed = bool(self.current_user)
        state = tk.NORMAL if is_authed else tk.DISABLED
        self.compose_button.config(state=state)
        self.schedule_button.config(state=state)
        self.run_button.config(state=state)
        self.reload_button.config(state=state)
        self.auth_button.config(text="Выйти" if is_authed else "Войти")
        if is_authed:
            self._set_status(f"Выполнен вход: {self.current_user}", busy=False)
        else:
            self._set_status("Требуется вход в систему.", busy=False)

    def _on_auth_button_clicked(self) -> None:
        if self.current_user:
            if messagebox.askyesno("Выход", "Выйти из системы?"):
                self.current_user = None
                self._apply_auth_state()
            return

        ok = self._startup_auth_flow()
        if not ok:
            self.current_user = None
            self._apply_auth_state()

    def _show_first_user_setup_dialog(self) -> bool:
        win = tk.Toplevel(self)
        win.title("Первичный запуск — создание пользователя")
        win.minsize(460, 260)
        win.transient(self)
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Пользователи не найдены. Создайте первого пользователя (рекомендуется роль admin).",
            wraplength=430,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 10))

        username_var = tk.StringVar()
        password_var = tk.StringVar()
        confirm_var = tk.StringVar()
        role_var = tk.StringVar(value="admin")

        form = ttk.Frame(frame)
        form.pack(fill=tk.X)

        def add_row(row: int, label: str, widget: tk.Widget) -> None:
            ttk.Label(form, text=label, width=14, anchor=tk.W).grid(row=row, column=0, sticky="w", pady=4)
            widget.grid(row=row, column=1, sticky="ew", pady=4)

        form.columnconfigure(1, weight=1)
        add_row(0, "Логин:", ttk.Entry(form, textvariable=username_var))
        add_row(1, "Пароль:", ttk.Entry(form, textvariable=password_var, show="*"))
        add_row(2, "Повтор:", ttk.Entry(form, textvariable=confirm_var, show="*"))
        add_row(3, "Роль:", ttk.Combobox(form, textvariable=role_var, values=("admin", "user"), state="readonly"))

        status_var = tk.StringVar(value="")
        status_label = ttk.Label(frame, textvariable=status_var, foreground="#AA0000")
        status_label.pack(anchor=tk.W, pady=(10, 0))

        result: dict[str, bool] = {"ok": False}

        def on_create() -> None:
            username = username_var.get().strip()
            pwd = password_var.get()
            conf = confirm_var.get()
            if not username:
                status_var.set("Введите логин.")
                return
            if not pwd or len(pwd.strip()) < 6:
                status_var.set("Пароль должен быть не короче 6 символов.")
                return
            if pwd != conf:
                status_var.set("Пароли не совпадают.")
                return
            try:
                create_user(username, pwd, role=role_var.get().strip() or "admin")
            except Exception as exc:  # noqa: BLE001
                status_var.set(f"Не удалось создать пользователя: {exc}")
                return
            result["ok"] = True
            win.destroy()

        def on_cancel() -> None:
            result["ok"] = False
            win.destroy()

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="Создать", command=on_create).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Отмена", command=on_cancel).pack(side=tk.LEFT, padx=(8, 0))

        win.protocol("WM_DELETE_WINDOW", on_cancel)
        self.wait_window(win)
        return bool(result["ok"])

    def _show_login_dialog(self) -> str | None:
        win = tk.Toplevel(self)
        win.title("Вход в систему")
        win.minsize(420, 220)
        win.transient(self)
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Введите логин и пароль для доступа к функциям HR‑сервиса.",
            wraplength=390,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 10))

        username_var = tk.StringVar()
        password_var = tk.StringVar()

        form = ttk.Frame(frame)
        form.pack(fill=tk.X)
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text="Логин:", width=12, anchor=tk.W).grid(row=0, column=0, sticky="w", pady=4)
        username_entry = ttk.Entry(form, textvariable=username_var)
        username_entry.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Пароль:", width=12, anchor=tk.W).grid(row=1, column=0, sticky="w", pady=4)
        password_entry = ttk.Entry(form, textvariable=password_var, show="*")
        password_entry.grid(row=1, column=1, sticky="ew", pady=4)

        status_var = tk.StringVar(value="")
        status_label = ttk.Label(frame, textvariable=status_var, foreground="#AA0000")
        status_label.pack(anchor=tk.W, pady=(10, 0))

        result: dict[str, str | None] = {"user": None}

        def on_login() -> None:
            username = username_var.get().strip()
            pwd = password_var.get()
            if not username or not pwd:
                status_var.set("Введите логин и пароль.")
                return
            try:
                user = authenticate(username, pwd)
            except Exception as exc:  # noqa: BLE001
                status_var.set(f"Ошибка входа: {exc}")
                return
            if not user:
                status_var.set("Неверный логин или пароль.")
                password_var.set("")
                password_entry.focus_set()
                return
            result["user"] = user.username
            win.destroy()

        def on_cancel() -> None:
            result["user"] = None
            win.destroy()

        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(buttons, text="Войти", command=on_login).pack(side=tk.LEFT)
        ttk.Button(buttons, text="Отмена", command=on_cancel).pack(side=tk.LEFT, padx=(8, 0))

        win.protocol("WM_DELETE_WINDOW", on_cancel)
        username_entry.focus_set()
        username_entry.bind("<Return>", lambda _e: password_entry.focus_set())
        password_entry.bind("<Return>", lambda _e: on_login())
        self.wait_window(win)
        return result["user"]

    # ---------- Обработчики событий ----------
    def _on_run_parser_clicked(self) -> None:
        if self.parser_thread and self.parser_thread.is_alive():
            messagebox.showinfo(
                "Парсер уже запущен",
                "Парсер вакансий уже выполняется. Дождитесь окончания работы.",
            )
            return

        links_path = Path(LINKS_FILE)
        if not links_path.exists():
            messagebox.showerror(
                "Файл ссылок не найден",
                f"Файл со ссылками не найден:\n{links_path}\n\n"
                "Создайте файл Links.txt с ссылками на работодателя S7 на hh.ru.",
            )
            return

        self._set_status("Запуск парсера вакансий...", busy=True)
        self.run_button.config(state=tk.DISABLED)
        self._reset_progress()
        self._start_progress_polling()

        # Работаем в директории скрипта, как и в vacancy_agent.main()
        script_dir = Path(__file__).resolve().parent
        os.chdir(script_dir)

        def worker() -> None:
            try:
                agent = VacancyParserAgent()
                vacancies = agent.run(progress_callback=self._progress_callback)
            except Exception as exc:  # noqa: BLE001
                self.after(
                    0,
                    lambda: self._on_parser_failed(exc),
                )
                return

            self.after(
                0,
                lambda: self._on_parser_finished(vacancies),
            )

        self.parser_thread = threading.Thread(target=worker, daemon=True)
        self.parser_thread.start()

    def _on_reload_clicked(self) -> None:
        self._load_vacancies_from_file(initial=False)

    def _progress_callback(self, done: int, total: int) -> None:
        # Вызывается из фонового потока, поэтому только обновляем простые значения
        self.progress_done = done
        self.progress_total = total

    # ---------- Логика загрузки / обновления данных ----------
    def _load_vacancies_from_file(self, initial: bool = False) -> None:
        output_path = Path(OUTPUT_FILE)
        if not output_path.exists():
            if initial:
                self._set_status(
                    "База вакансий ещё не создана. Нажмите «Запустить парсер».", busy=False
                )
            else:
                messagebox.showinfo(
                    "Файл результатов не найден",
                    f"Файл с результатами не найден:\n{output_path}\n\n"
                    "Сначала запустите парсер вакансий.",
                )
            self._update_table([])
            return

        try:
            raw = output_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError("Неверный формат файла с вакансиями")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror(
                "Ошибка чтения файла",
                f"Не удалось прочитать файл с вакансиями:\n{output_path}\n\n{exc}",
            )
            self._update_table([])
            return

        self.vacancies = data
        self._update_table(self.vacancies)
        self._set_status("Данные загружены из файла.", busy=False)

    def _update_table(self, vacancies: list[dict]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for vac in vacancies:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    vac.get("title", ""),
                    vac.get("area", ""),
                    vac.get("salary", ""),
                    vac.get("responses", ""),
                    vac.get("experience", ""),
                    vac.get("employment", ""),
                    vac.get("schedule", ""),
                ),
            )

        self.counter_var.set(f"Вакансий в базе: {len(vacancies)}")

    # ---------- Обновление статуса ----------
    def _set_status(self, text: str, busy: bool) -> None:
        self.status_var.set(text)
        self.status_label.configure(foreground="#AA0000" if busy else "#007700")

    def _reset_progress(self) -> None:
        self.progress_total = 0
        self.progress_done = 0
        self.progress_var.set("")

    def _start_progress_polling(self) -> None:
        self._poll_progress()

    def _poll_progress(self) -> None:
        if self.parser_thread and self.parser_thread.is_alive():
            if self.progress_total > 0:
                percent = int(self.progress_done / self.progress_total * 100)
                if percent > 100:
                    percent = 100
                self.progress_var.set(f"{percent}%")
            else:
                self.progress_var.set("")
            self.after(200, self._poll_progress)
        else:
            # Поток завершился — дальнейшее состояние установит обработчик завершения
            return

    def _on_parser_finished(self, vacancies: list[dict]) -> None:
        self.vacancies = vacancies
        self._update_table(self.vacancies)
        # Обновляем подпись правее статуса: сколько записей загружено
        self.progress_var.set(f"Загружено записей: {len(self.vacancies)}")
        self.progress_total = 0
        self.progress_done = 0
        self._set_status(
            f"Парсинг завершён. Собрано вакансий: {len(self.vacancies)}.", busy=False
        )
        self.run_button.config(state=tk.NORMAL)

    def _on_parser_failed(self, exc: Exception) -> None:
        self._set_status("Ошибка при выполнении парсера.", busy=False)
        self.run_button.config(state=tk.NORMAL)
        messagebox.showerror(
            "Ошибка парсера",
            f"Во время выполнения парсера возникла ошибка:\n\n{exc}",
        )

    # ---------- Составление вакансии и расписание собеседований ----------
    def _on_compose_vacancy_clicked(self) -> None:
        """Открыть окно составления вакансии по запросу через локальную модель YandexGPT."""
        win = tk.Toplevel(self)
        win.title("Составление вакансии — YandexGPT")
        win.minsize(700, 500)

        # Центровка окна
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win.update_idletasks()
        width = 700
        height = 500
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Опишите запрос к вакансии (должность, профиль, требования, уровень, формат работы и т.п.):",
            wraplength=660,
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        query_text = tk.Text(frame, height=6, wrap="word")
        query_text.pack(fill=tk.X, expand=False, pady=(5, 10))

        controls = ttk.Frame(frame)
        controls.pack(fill=tk.X)

        status_var = tk.StringVar(value="")
        status_label = ttk.Label(controls, textvariable=status_var, foreground="#007700")
        status_label.pack(side=tk.LEFT)

        def set_local_status(msg: str, error: bool = False) -> None:
            status_var.set(msg)
            status_label.configure(foreground="#AA0000" if error else "#007700")

        result_frame = ttk.LabelFrame(frame, text="Сформированное описание вакансии")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        result_text = tk.Text(result_frame, wrap="word")
        result_text.pack(fill=tk.BOTH, expand=True)
        result_text.configure(state="disabled")

        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        def on_generate_clicked() -> None:
            prompt = query_text.get("1.0", "end").strip()
            if not prompt:
                messagebox.showwarning(
                    "Пустой запрос",
                    "Введите запрос (описание желаемой вакансии), чтобы сгенерировать текст.",
                )
                return

            set_local_status("Обращение к локальной модели YandexGPT...", error=False)

            def worker() -> None:
                try:
                    # Ленивая загрузка, чтобы предупреждения/зависимости LangChain
                    # не мешали старту GUI.
                    from yagpt_client import generate_vacancy

                    text = generate_vacancy(prompt)
                    docx_path = save_vacancy_to_docx(text)
                except Exception as exc:  # noqa: BLE001
                    self.after(
                        0,
                        lambda: set_local_status(
                            f"Ошибка генерации вакансии или DOCX: {exc}", error=True
                        ),
                    )
                    return

                def update_result() -> None:
                    result_text.configure(state="normal")
                    result_text.delete("1.0", "end")
                    result_text.insert("1.0", text or "Модель не вернула текст вакансии.")
                    result_text.configure(state="disabled")
                    set_local_status(
                        f"Генерация завершена. Файл DOCX сохранён: {docx_path}", error=False
                    )

                self.after(0, update_result)

            threading.Thread(target=worker, daemon=True).start()

        def on_copy_clicked() -> None:
            text = result_text.get("1.0", "end").strip()
            if not text:
                return
            self.clipboard_clear()
            self.clipboard_append(text)
            set_local_status("Текст вакансии скопирован в буфер обмена.", error=False)

        generate_button = ttk.Button(buttons_frame, text="Сгенерировать", command=on_generate_clicked)
        generate_button.pack(side=tk.LEFT)

        copy_button = ttk.Button(buttons_frame, text="Скопировать", command=on_copy_clicked)
        copy_button.pack(side=tk.LEFT, padx=(5, 0))

    def _on_schedule_clicked(self) -> None:
        """Пока только заглушка для будущего функционала расписания собеседований."""
        messagebox.showinfo(
            "Расписание собеседований",
            "Модуль просмотра расписания собеседований пока не реализован.\n"
            "Его можно будет подключить к HR‑календарю или внешней системе бронирования слотов.",
        )


    # ---------- Детальное окно вакансии ----------
    def _on_row_double_click(self, _event) -> None:
        item_id = self.tree.focus()
        if not item_id:
            return
        index = self.tree.index(item_id)
        if 0 <= index < len(self.vacancies):
            vacancy = self.vacancies[index]
            self._open_detail_window(vacancy)

    def _open_detail_window(self, vacancy: dict) -> None:
        win = tk.Toplevel(self)
        win.title(f"Вакансия — {vacancy.get('title', '')}")
        win.minsize(700, 500)

        # Центровка дочернего окна относительно основного
        self.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        win.update_idletasks()
        width = 700
        height = 500
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        win.geometry(f"{width}x{height}+{x}+{y}")

        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        def add_label_row(parent, label_text: str, value: str) -> None:
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=2)
            ttk.Label(row, text=label_text, width=18, anchor=tk.W, font=("Segoe UI", 9, "bold")).pack(
                side=tk.LEFT
            )
            ttk.Label(row, text=value, anchor=tk.W, wraplength=520, justify=tk.LEFT).pack(
                side=tk.LEFT, fill=tk.X, expand=True
            )

        add_label_row(frame, "Должность:", vacancy.get("title", ""))
        add_label_row(frame, "Город:", vacancy.get("area", ""))
        add_label_row(frame, "Зарплата:", vacancy.get("salary", ""))
        add_label_row(frame, "Опыт:", vacancy.get("experience", ""))
        add_label_row(frame, "Занятость:", vacancy.get("employment", ""))
        add_label_row(frame, "График:", vacancy.get("schedule", ""))

        # Ключевые навыки
        skills = vacancy.get("skills")
        if not skills:
            key_skills = vacancy.get("key_skills") or []
            if isinstance(key_skills, list):
                names = []
                for sk in key_skills:
                    name = (sk or {}).get("name")
                    if name:
                        names.append(name)
                skills = ", ".join(names)
        add_label_row(frame, "Ключевые навыки:", skills or "—")

        # Многострочные поля — требования, обязанности, условия
        text_frame = ttk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        def add_text_block(parent, title: str, content: str) -> None:
            block = ttk.LabelFrame(parent, text=title)
            block.pack(fill=tk.BOTH, expand=True, pady=4)
            txt = tk.Text(block, wrap="word", height=5)
            txt.pack(fill=tk.BOTH, expand=True)
            txt.insert("1.0", content or "—")
            txt.configure(state="disabled")

        add_text_block(text_frame, "Требования", vacancy.get("requirements", ""))
        add_text_block(text_frame, "Обязанности", vacancy.get("responsibilities", ""))
        add_text_block(text_frame, "Условия", vacancy.get("conditions", ""))

        link = vacancy.get("link", "")
        if link:
            link_frame = ttk.Frame(frame)
            link_frame.pack(fill=tk.X, pady=(8, 0))
            ttk.Label(
                link_frame,
                text="Ссылка на вакансию:",
                font=("Segoe UI", 9, "bold"),
            ).pack(side=tk.LEFT)
            ttk.Label(
                link_frame,
                text=link,
                foreground="#0055aa",
                cursor="hand2",
                wraplength=520,
                justify=tk.LEFT,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True)


def main() -> None:
    # Гарантируем запуск из директории проекта, чтобы относительные пути совпадали
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)

    app = HRApp()
    app.mainloop()


if __name__ == "__main__":
    main()

