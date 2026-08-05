import streamlit as st

# セッション状態の初期化（ユーザーデータベースと申請データを保持）
if "users" not in st.session_state:
    st.session_state.users = {
        "tsunoda": {
            "password": "password123",
            "name": "角田 悠",
            "role": "sales",
        },
        "watanabe": {
            "password": "password123",
            "name": "渡辺 湯大",
            "role": "tech_chief",
        },
        "sato": {
            "password": "password123",
            "name": "佐藤 環境",
            "role": "env_staff",
        },
        "admin": {"password": "1234", "name": "管理者", "role": "admin"},
    }

if "orders" not in st.session_state:
    st.session_state.orders = [
        {
            "id": 1,
            "client": "株式会社水栄",
            "job_title": (
                "企平第5号 二宮町二宮1281番地付近配水管切回工事(電線共同溝)"
            ),
            "estimate_no": "M26-1776",
            "sales_rep": "角田 悠",
            "related_depts": ["水質課"],
            "details": (
                "1. UCR 秦野中井IC南 土砂検定溶出28項目+pH 含有9項目+農用地銅、砒素\n2. 5地点混合1検体"
            ),
            "sales_approved": False,
            "tech_approved": False,
            "env_approved": False,
        }
    ]

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.name = ""

# 権限名の定義
role_names = {
    "sales": "営業課",
    "tech_chief": "水質課",
    "env_staff": "環境業務係",
    "admin": "システム管理者",
}

# --- 1. ログイン画面 ---
if not st.session_state.logged_in:
    st.title("🔐 受注書・調査指示書システム ログイン")

    with st.form("login_form"):
        username_input = st.text_input("ユーザーID (例: admin / tsunoda)")
        password_input = st.text_input("パスワード", type="password")
        submit_btn = st.form_submit_button("ログイン")

        if submit_btn:
            users_db = st.session_state.users
            if (
                username_input in users_db
                and users_db[username_input]["password"] == password_input
            ):
                st.session_state.logged_in = True
                st.session_state.username = username_input
                st.session_state.name = users_db[username_input]["name"]
                st.session_state.role = users_db[username_input]["role"]
                st.success(
                    f"ようこそ、{st.session_state.name}さん！ログインしました。"
                )
                st.rerun()
            else:
                st.error("ユーザーIDまたはパスワードが間違っています。")

# --- 2. ログイン後のメイン画面 ---
else:
    # サイドバーにユーザー情報とメニュー切り替えを表示
    st.sidebar.title(f"👤 {st.session_state.name} さん")
    st.sidebar.text(
        f"所属: {role_names.get(st.session_state.role, '不明')}"
    )
    st.sidebar.markdown("---")

    menu_options = [
        "📋 指示書一覧（全件閲覧）",
        "✍️ 新規指示書作成",
        "✅ 承認・進捗管理",
    ]
    if st.session_state.role == "admin":
        menu_options.append("⚙️ 管理者画面（ユーザー管理）")

    selected_menu = st.sidebar.radio("📌 メニュー切り替え", menu_options)

    st.sidebar.markdown("---")
    if st.sidebar.button("ログアウト"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.name = ""
        st.rerun()

    st.title("📋 受注書兼調査指示書 管理システム")

    # --- 機能1：新規作成・申請（営業課・管理者向け） ---
    if selected_menu == "✍️ 新規指示書作成":
        if st.session_state.role not in ["sales", "admin"]:
            st.warning("新規作成は「営業課」または「管理者」のみ可能です。")
        else:
            st.info(
                "【新規作成】 受注書・調査指示書の作成・申請を行います。"
            )

            with st.form("order_form"):
                st.subheader("1. 基本情報・関連部署")
                col1, col2 = st.columns(2)
                with col1:
                    reception_date = st.date_input("受付日")
                    client_name = st.text_input("顧客名", "株式会社水栄")
                with col2:
                    sales_rep = st.text_input(
                        "担当営業員", value=st.session_state.name
                    )
                    estimate_no = st.text_input(
                        "見積り番号", value="M26-1776"
                    )

                st.markdown(
                    "**関連部署（対応部署・複数選択可）**"
                )
                chk_tech = st.checkbox("水質課", value=True)
                chk_env = st.checkbox("環境業務係")

                st.subheader("2. 業務内容・スケジュール")
                job_title = st.text_input(
                    "業務件名",
                    "企平第5号 二宮町二宮1281番地付近配水管切回工事(電線共同溝)",
                )
                measurement_date = st.date_input("測定予定日")

                st.subheader("3. 測定項目チェック")
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    ch_noise = st.checkbox("騒音測定")
                    ch_vibration = st.checkbox("振動測定")
                with col_b:
                    ch_odor = st.checkbox("悪臭測定")
                    ch_soil = st.checkbox("土壌汚染調査", value=True)
                with col_c:
                    ch_water = st.checkbox("水質")

                st.subheader("4. 詳細仕様")
                details = st.text_area(
                    "受注内容・特記事項",
                    "1. UCR 秦野中井IC南 土砂検定溶出28項目+pH 含有9項目+農用地銅、砒素\n2. 5地点混合1検体",
                )

                submitted = st.form_submit_button("作成・申請する")
                if submitted:
                    selected_depts = []
                    if chk_tech:
                        selected_depts.append("水質課")
                    if chk_env:
                        selected_depts.append("環境業務係")

                    if not selected_depts:
                        st.warning(
                            "関連部署を少なくとも1つ選択してください。"
                        )
                    else:
                        new_order = {
                            "id": len(st.session_state.orders) + 1,
                            "client": client_name,
                            "job_title": job_title,
                            "estimate_no": estimate_no,
                            "sales_rep": sales_rep,
                            "related_depts": selected_depts,
                            "details": details,
                            "sales_approved": False,
                            "tech_approved": False,
                            "env_approved": False,
                        }
                        st.session_state.orders.append(new_order)
                        st.success(
                            "指示書を作成しました。「指示書一覧」または「承認・進捗管理」から確認できます。"
                        )

    # --- 機能2：指示書一覧（自部署・他部署分割表示 ＆ 受注内容表示） ---
    elif selected_menu == "📋 指示書一覧（全件閲覧）":
        st.subheader("📋 指示書一覧（閲覧モード）")
        st.write(
            "登録されている指示書を自部署の関連案件と他部署の案件に分けて表示しています。"
        )

        my_dept_name = role_names.get(st.session_state.role, "")

        # 案件を「自部署関連」と「他部署」に分類
        my_dept_orders = []
        other_dept_orders = []

        for o in st.session_state.orders:
            # 営業課と管理者は「自部署」扱い（すべての案件を詳細閲覧可能）として整理
            is_my_dept = (
                st.session_state.role in ["sales", "admin"]
                or my_dept_name in o["related_depts"]
            )
            if is_my_dept:
                my_dept_orders.append(o)
            else:
                other_dept_orders.append(o)

        # 1. 自部署の関連案件
        st.markdown("### 📌 自部署の関連案件")
        if not my_dept_orders:
            st.info("現在、自部署に関連する案件はありません。")
        else:
            for o in my_dept_orders:
                depts_str = ", ".join(o["related_depts"])
                with st.expander(
                    f"ID: {o['id']} | 顧客: {o['client']}様 | 件名: {o['job_title']}"
                ):
                    st.markdown(
                        f"- **見積り番号**: {o['estimate_no']}  \n"
                        f"- **担当営業**: {o['sales_rep']}  \n"
                        f"- **関連部署**: {depts_str}"
                    )
                    st.markdown("---")
                    st.markdown("**📝 受注内容・特記事項:**")
                    st.text(o.get("details", "特記事項なし"))
                    st.markdown("---")
                    st.markdown("##### 📌 各段階の承認状況")
                    st.write(
                        f"1. 営業課 承認: {'✅ 承認済み' if o['sales_approved'] else '⏳ 未承認'}"
                    )
                    if "水質課" in o["related_depts"]:
                        st.write(
                            f"2. 水質課 承認: {'✅ 承認済み' if o['tech_approved'] else '⏳ 未承認'}"
                        )
                    if "環境業務係" in o["related_depts"]:
                        st.write(
                            f"3. 環境業務係 承認: {'✅ 承認済み' if o['env_approved'] else '⏳ 未承認'}"
                        )

        st.markdown("---")

        # 2. 他部署の案件
        st.markdown("### 📁 他部署の案件（閲覧のみ）")
        if not other_dept_orders:
            st.info("他の部署の案件はありません。")
        else:
            for o in other_dept_orders:
                depts_str = ", ".join(o["related_depts"])
                with st.expander(
                    f"ID: {o['id']} | 顧客: {o['client']}様 | 件名: {o['job_title']} （他部署案件）"
                ):
                    st.warning(
                        "この指示書は他部署の案件です。詳細（受注内容など）は制限されています。"
                    )
                    st.markdown(
                        f"- **見積り番号**: {o['estimate_no']}  \n"
                        f"- **関連部署**: {depts_str}"
                    )
                    st.markdown("##### 📌 各段階の承認状況")
                    st.write(
                        f"1. 営業課 承認: {'✅ 承認済み' if o['sales_approved'] else '⏳ 未承認'}"
                    )
                    if "水質課" in o["related_depts"]:
                        st.write(
                            f"2. 水質課 承認: {'✅ 承認済み' if o['tech_approved'] else '⏳ 未承認'}"
                        )
                    if "環境業務係" in o["related_depts"]:
                        st.write(
                            f"3. 環境業務係 承認: {'✅ 承認済み' if o['env_approved'] else '⏳ 未承認'}"
                        )

    # --- 機能3：承認・進捗管理（各権限に応じたチェック欄） ---
    elif selected_menu == "✅ 承認・進捗管理":
        st.subheader("✅ 承認・進捗管理ダッシュボード")
        st.info(
            "ご自身の権限に応じた承認チェックを行うことができます。（※水質課・環境業務係の承認は、営業課の承認が完了したあとに有効になります）"
        )

        for idx, o in enumerate(st.session_state.orders):
            my_dept_name = role_names.get(st.session_state.role, "")
            is_relevant = (
                st.session_state.role in ["sales", "admin"]
                or my_dept_name in o["related_depts"]
            )

            if not is_relevant:
                continue

            depts_str = ", ".join(o["related_depts"])
            st.markdown(
                f"**[ID: {o['id']}] 顧客: {o['client']} 様** | 件名: {o['job_title']} (関連部署: {depts_str})"
            )

            col1, col2, col3 = st.columns(3)

            # 1. 営業課の承認ボタン
            with col1:
                can_sales_op = st.session_state.role in ["sales", "admin"]
                sales_status = st.checkbox(
                    "営業課 承認済",
                    value=o["sales_approved"],
                    key=f"sales_chk_{o['id']}",
                    disabled=not can_sales_op,
                )
                if sales_status != o["sales_approved"] and can_sales_op:
                    st.session_state.orders[idx]["sales_approved"] = (
                        sales_status
                    )
                    st.rerun()

            # 2. 水質課の承認ボタン
            with col2:
                in_tech = "水質課" in o["related_depts"]
                can_tech_op = (
                    st.session_state.role in ["tech_chief", "admin"]
                    and in_tech
                ) or st.session_state.role == "admin"
                tech_status = st.checkbox(
                    "水質課 承認済",
                    value=o["tech_approved"],
                    key=f"tech_chk_{o['id']}",
                    disabled=not in_tech
                    or not o["sales_approved"]
                    or (
                        st.session_state.role == "tech_chief"
                        and not can_tech_op
                    ),
                )
                if tech_status != o["tech_approved"] and in_tech:
                    st.session_state.orders[idx]["tech_approved"] = tech_status
                    st.rerun()
                elif not in_tech:
                    st.text("(水質課 対象外)")

            # 3. 環境業務係の承認ボタン
            with col3:
                in_env = "環境業務係" in o["related_depts"]
                can_env_op = (
                    st.session_state.role in ["env_staff", "admin"] and in_env
                ) or st.session_state.role == "admin"
                env_status = st.checkbox(
                    "環境業務係 承認済",
                    value=o["env_approved"],
                    key=f"env_chk_{o['id']}",
                    disabled=not in_env
                    or not o["sales_approved"]
                    or (st.session_state.role == "env_staff" and not can_env_op),
                )
                if env_status != o["env_approved"] and in_env:
                    st.session_state.orders[idx]["env_approved"] = env_status
                    st.rerun()
                elif not in_env:
                    st.text("(環境業務係 対象外)")

            st.write("---")

    # --- 機能4：管理者画面（ユーザー追加・削除） ---
    elif selected_menu == "⚙️ 管理者画面（ユーザー管理）":
        if st.session_state.role != "admin":
            st.error("この画面はシステム管理者のみアクセスできます。")
        else:
            st.subheader("⚙️ 【管理者専用】ユーザーアカウント管理")

            with st.form("add_user_form"):
                st.write("➕ 新規ユーザーの追加と所属（権限）付与")
                new_uid = st.text_input("新しいユーザーID (例: suzuki)")
                new_pwd = st.text_input(
                    "パスワード", type="password", value="password123"
                )
                new_name = st.text_input("氏名 (例: 鈴木 一郎)")
                new_role = st.selectbox(
                    "所属部署（権限）",
                    options=["sales", "tech_chief", "env_staff", "admin"],
                    format_func=lambda x: role_names[x],
                )

                add_btn = st.form_submit_button("ユーザーを追加する")
                if add_btn:
                    if new_uid in st.session_state.users:
                        st.error("そのユーザーIDはすでに存在します。")
                    elif not new_uid or not new_name:
                        st.warning("ユーザーIDと氏名を入力してください。")
                    else:
                        st.session_state.users[new_uid] = {
                            "password": new_pwd,
                            "name": new_name,
                            "role": new_role,
                        }
                        st.success(
                            f"ユーザー「{new_name} ({new_uid})」を追加しました！"
                        )
                        st.rerun()

            st.markdown("---")
            st.subheader("👥 登録済みユーザー一覧・削除")

            for uid, info in list(st.session_state.users.items()):
                r_name = role_names.get(info["role"], info["role"])
                col_u1, col_u2 = st.columns([3, 1])
                with col_u1:
                    st.text(
                        f"ID: {uid} | 氏名: {info['name']} | 所属: {r_name}"
                    )
                with col_u2:
                    if uid == "admin":
                        st.text("削除不可")
                    else:
                        if st.button("🗑️ 削除", key=f"del_user_{uid}"):
                            del st.session_state.users[uid]
                            st.warning(
                                f"ユーザー「{info['name']} ({uid})」を削除しました。"
                            )
                            st.rerun()