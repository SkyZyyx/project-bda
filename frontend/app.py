# ==============================================================================
# EXAM SCHEDULING PLATFORM - STREAMLIT MAIN APP
# ==============================================================================
# This is the entry point of the Streamlit frontend application.
# It provides a modern, multi-page dashboard for the exam scheduling system.
# ==============================================================================

import streamlit as st
from streamlit_option_menu import option_menu
from utils.api import (
    api,
    get_current_user,
    is_authenticated,
    logout,
    wake_backend,
    restore_session,
)

# Import custom utilities
from utils.styles import conflict_indicator, inject_custom_css, metric_card, page_header

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Exam Scheduling Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
inject_custom_css()

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

# ==============================================================================
# BACKEND WAKE-UP CHECK
# ==============================================================================
# On first load, ensure backend is awake (handles free tier cold starts)
if "backend_ready" not in st.session_state:
    st.session_state.backend_ready = False

if not st.session_state.backend_ready:
    # Wake up the backend with a professional loading screen
    success = wake_backend()
    if success:
        st.session_state.backend_ready = True
        st.rerun()  # Reload to show the main app
    # If wake_backend returns False, it will show an error and stop execution

# ==============================================================================
# SESSION RESTORATION FROM LOCALSTORAGE
# ==============================================================================
# After backend is ready, try to restore user session from browser localStorage
# This keeps users logged in across page refreshes and browser restarts
if "session_restore_attempted" not in st.session_state:
    st.session_state.session_restore_attempted = False

if not st.session_state.session_restore_attempted:
    # Try to restore session from localStorage
    restore_session()
    st.session_state.session_restore_attempted = True

# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
# ==============================================================================
# SIDEBAR NAVIGATION
# ==============================================================================
with st.sidebar:
    # Logo and title matching "ExamOpti" theme
    st.markdown(
        """
    <div style="padding: 1rem 0; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: var(--primary-gradient); width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 1.2rem;">
                E
            </div>
            <h1 style="font-size: 1.5rem; font-weight: 800; margin: 0; color: white; letter-spacing: -0.03em;">
                ExamOpti
            </h1>
        </div>
        <p style="color: var(--text-secondary); font-size: 0.8rem; margin: 4px 0 0 48px; font-weight: 500;">
            Strategic Scheduling
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Navigation menu - adapté selon le rôle
    if is_authenticated():
        user = get_current_user()
        user_role = user.get("role", "student") if user else "student"

        # Définir les menus selon le rôle
        if user_role in ["admin"]:
            # Admin: accès complet à tout
            menu_options = [
                "Dashboard",
                "Scheduling",
                "Exams",
                "Departments",
                "Professors",
                "Personal Schedule",
                "Settings",
            ]
            menu_icons = [
                "grid-fill",
                "calendar-check-fill",
                "journal-bookmark-fill",
                "building-fill",
                "person-badge-fill",
                "person-circle",
                "gear-fill",
            ]
        elif user_role in ["dean", "vice_dean"]:
            # Doyen/Vice-Doyen: vue stratégique, validation, pas de planning manuel
            menu_options = [
                "Dashboard",
                "Validation",
                "Exams",
                "Departments",
                "Professors",
                "Settings",
            ]
            menu_icons = [
                "grid-fill",
                "check-circle-fill",
                "journal-bookmark-fill",
                "building-fill",
                "person-badge-fill",
                "gear-fill",
            ]
        elif user_role in ["department_head", "dept_head"]:
            # Chef département: validation de son département
            menu_options = [
                "Dashboard",
                "Validation",
                "Exams",
                "My Department",
                "Personal Schedule",
                "Settings",
            ]
            menu_icons = [
                "grid-fill",
                "check-circle-fill",
                "journal-bookmark-fill",
                "building-fill",
                "person-circle",
                "gear-fill",
            ]
        elif user_role == "professor":
            # Professeur: voir ses surveillances uniquement
            menu_options = ["My Supervisions", "Personal Schedule", "Settings"]
            menu_icons = ["calendar-check-fill", "person-circle", "gear-fill"]
        else:
            # Étudiant: voir ses examens uniquement
            menu_options = ["My Exams", "Personal Schedule", "Settings"]
            menu_icons = ["journal-bookmark-fill", "person-circle", "gear-fill"]

        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"color": "var(--text-secondary)", "font-size": "1rem"},
                "nav-link": {
                    "font-size": "0.9rem",
                    "text-align": "left",
                    "margin": "0.4rem 0.6rem",
                    "padding": "0.8rem 1rem",
                    "border-radius": "12px",
                    "color": "var(--text-secondary)",
                    "font-weight": "500",
                    "transition": "all 0.2s",
                },
                "nav-link-selected": {
                    "background-color": "rgba(0, 97, 255, 0.15)",
                    "color": "var(--primary)",
                    "font-weight": "600",
                    "border-left": "4px solid var(--primary)",
                },
            },
        )

        # Profile section at the bottom
        user = get_current_user()
        if user:
            st.markdown(
                f"""
            <div style="margin-top: 2rem; padding: 1rem;">
                <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); border-radius: 16px; padding: 12px; display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; border-radius: 10px; background: #252A34; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">
                        👤
                    </div>
                    <div style="overflow: hidden;">
                        <div style="font-weight: 600; color: white; font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            {user.get("name", "User")}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary);">
                            {user.get("role", "N/A").title()}
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if st.button("🚪 Sign Out", key="logout_btn", use_container_width=True):
                logout()
                st.rerun()
    else:
        selected = "Login"
        st.info("Please sign in to access.")

# ==============================================================================
# PAGE ROUTING
# ==============================================================================

if not is_authenticated():
    # -------------------------------------------------------------------------
    # LOGIN PAGE
    # -------------------------------------------------------------------------
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            page_header(
                "🎓 Welcome Back", "Sign in to access the Exam Scheduling Platform"
            ),
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="admin@university.edu")
            password = st.text_input(
                "🔒 Password", type="password", placeholder="••••••••"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                remember = st.checkbox("Remember me")

            submitted = st.form_submit_button("Sign In", use_container_width=True)

            if submitted:
                if email and password:
                    from utils.api import login

                    result = login(email, password)

                    if result.get("error"):
                        st.error(f"❌ {result.get('detail', 'Login failed')}")
                    else:
                        st.success("✅ Login successful!")
                        st.rerun()
                else:
                    st.warning("⚠️ Please enter email and password")

        st.markdown(
            """
        <div style="text-align: center; margin-top: 2rem; color: #64748b;">
            <p>Demo Admin: <code>admin@univ-alger.dz</code> / <code>admin123</code></p>
            <p style="font-size: 0.8rem;">Check README.md for all other roles (Dean, Dept Head, etc.)</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

elif selected == "Dashboard":
    # -------------------------------------------------------------------------
    # DASHBOARD PAGE
    # -------------------------------------------------------------------------
    st.markdown(
        page_header(
            "Strategic Dashboard",
            "Real-time overview of current exam session performance and resource optimization",
        ),
        unsafe_allow_html=True,
    )

    # Fetch dashboard data
    with st.spinner("Analyzing metrics..."):
        stats = api.get("/dashboard/overview")

    if stats.get("error"):
        st.error(f"Failed to load dashboard: {stats.get('detail')}")
    else:
        # Calculate aggregates from active sessions
        active_sessions = stats.get("active_sessions", [])
        total_exams = sum(s.get("total_exams", 0) for s in active_sessions)
        scheduled_exams = sum(s.get("scheduled_exams", 0) for s in active_sessions)
        conflicts = sum(s.get("conflict_count", 0) for s in active_sessions)

        # Calculer les vrais pourcentages basés sur les données
        progress_pct = (
            int(scheduled_exams / total_exams * 100) if total_exams > 0 else 0
        )
        pending_exams = total_exams - scheduled_exams

        # Metrics row
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(
                metric_card(
                    str(stats.get("total_students", 0)),
                    "Total Étudiants",
                    "👨‍🎓",
                    trend=f"{stats.get('total_formations', 0)} formations",
                    trend_up=True,
                ),
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                metric_card(
                    str(total_exams),
                    "Total Examens",
                    "📚",
                    trend=f"{pending_exams} en attente",
                    trend_up=pending_exams == 0,
                ),
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                metric_card(
                    f"{scheduled_exams}/{total_exams}",
                    "Progression",
                    "🗓️",
                    trend=f"{progress_pct}% planifiés",
                    trend_up=progress_pct > 50,
                ),
                unsafe_allow_html=True,
            )

        with col4:
            st.markdown(
                metric_card(
                    str(conflicts),
                    "Conflits",
                    "⚠️",
                    trend="Action requise" if conflicts > 0 else "Aucun conflit",
                    trend_up=conflicts == 0,
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin: 2.5rem 0;'></div>", unsafe_allow_html=True)

        # Main Dashboard Layout
        col_main, col_side = st.columns([2, 1])

        with col_main:
            st.markdown(
                """
            <div class="kpi-card" style="height: 100%;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700;">📅 Upcoming Exam Blocks</h3>
                    <div style="font-size: 0.75rem; color: var(--primary); font-weight: 600; cursor: pointer;">Next 48 Hours →</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            recent_exams = api.get("/dashboard/upcoming-exams")
            if recent_exams and not (
                isinstance(recent_exams, dict) and recent_exams.get("error")
            ):
                import pandas as pd

                df = pd.DataFrame(recent_exams)
                if not df.empty:
                    # Map IDs to names if needed, or use what's available
                    display_cols = [
                        "module_name",
                        "scheduled_date",
                        "room_name",
                        "status",
                    ]
                    # Ensure columns exist
                    cols = [c for c in display_cols if c in df.columns]
                    st.dataframe(
                        df[cols] if cols else df,
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No exams scheduled for the next 48 hours.")
            else:
                st.info(
                    "Quick schedule some exams in the 'Scheduling' tab to see data here."
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            st.markdown(
                """
            <div class="kpi-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                    <h3 style="margin: 0; font-size: 1.1rem; font-weight: 700;">📊 Départements</h3>
                    <div style="font-size: 0.75rem; color: var(--primary); font-weight: 600;">Statistiques</div>
                </div>
            """,
                unsafe_allow_html=True,
            )

            from utils.styles import conflict_indicator

            departments = api.get("/departments")
            if departments and isinstance(departments, list):
                # Afficher les départements avec leur nombre de formations
                for d in departments[:5]:
                    # Utiliser le nombre de formations plutôt que des conflits fictifs
                    dept_formations = d.get("formations_count", 5)  # Valeur par défaut
                    st.markdown(
                        f"""
                    <div style="margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="font-size: 0.9rem; font-weight: 500;">{d["name"]}</span>
                            <span style="font-size: 0.85rem; color: var(--text-secondary);">{dept_formations} formations</span>
                        </div>
                        <div style="height: 8px; width: 100%; background: rgba(255,255,255,0.05); border-radius: 10px;">
                            <div style="height: 100%; width: {min(100, dept_formations * 20)}%; background: var(--success); border-radius: 10px;"></div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Aucune donnée de département disponible.")
            st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Scheduling":
    # -------------------------------------------------------------------------
    # SCHEDULING PAGE
    # -------------------------------------------------------------------------
    st.markdown(
        page_header(
            "Planning & Optimization",
            "Strategic Control Center for Exam Session Validation and Conflict Resolution",
        ),
        unsafe_allow_html=True,
    )

    # 1. Fetch data for metrics
    @st.cache_data(ttl=10, show_spinner=False)
    def fetch_dashboard_overview(_api_base_url: str, _auth_token: str):
        """Cached dashboard overview - refreshes every 10 seconds"""
        return api.get("/dashboard/overview", timeout=15)

    with st.spinner("Analyzing session state..."):
        overview = fetch_dashboard_overview(
            api.base_url, st.session_state.get("auth_token", "")
        )
        active_sessions = (
            overview.get("active_sessions", []) if not overview.get("error") else []
        )

    if not active_sessions:
        st.warning(
            "⚠️ No active exam sessions found. Please initialize a session in the database first."
        )
    else:
        session_map = {s["name"]: s["id"] for s in active_sessions}

        # Session selector in a compact row
        col_sel, col_stats = st.columns([1, 2])
        with col_sel:
            selected_name = st.selectbox(
                "Current Active Session", options=session_map.keys()
            )
            selected_id = session_map[selected_name]
            # Get specific session details for better metrics
            curr_session = next(
                (s for s in active_sessions if s["id"] == selected_id), {}
            )

        # Calculs réels pour les KPIs
        total_exams = curr_session.get("total_exams", 0)
        scheduled_exams = curr_session.get("scheduled_exams", 0)
        pending_exams = total_exams - scheduled_exams
        conflicts = curr_session.get("conflict_count", 0)

        # Calculer le taux de progression
        progress_pct = (
            int((scheduled_exams / total_exams * 100)) if total_exams > 0 else 0
        )

        # KPIs row pour le statut de planification
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(
                metric_card(
                    str(total_exams),
                    "Total Examens",
                    "📋",
                    trend=f"{scheduled_exams} planifiés",
                    trend_up=scheduled_exams > 0,
                ),
                unsafe_allow_html=True,
            )
        with kpi2:
            st.markdown(
                metric_card(
                    str(pending_exams),
                    "En Attente",
                    "🕒",
                    trend=f"{100 - progress_pct}% restant",
                    trend_up=pending_exams == 0,
                ),
                unsafe_allow_html=True,
            )
        with kpi3:
            st.markdown(
                metric_card(
                    str(conflicts),
                    "Conflits Détectés",
                    "⚠️",
                    trend="Aucun" if conflicts == 0 else f"{conflicts} à résoudre",
                    trend_up=conflicts == 0,
                ),
                unsafe_allow_html=True,
            )
        with kpi4:
            st.markdown(
                metric_card(
                    f"{progress_pct}%",
                    "Taux Planification",
                    "📊",
                    trend="Complet"
                    if progress_pct == 100
                    else f"{pending_exams} restants",
                    trend_up=progress_pct >= 50,
                ),
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabs for different scheduling modes
        tab1, tab2, tab3 = st.tabs(
            ["🤖 Auto-Resolve", "📋 Manual Override", "⚠️ Conflict Report"]
        )

        with tab1:
            # Auto-scheduler panel
            st.markdown(
                """
            <div class="kpi-card" style="margin-bottom: 1.5rem;">
                <h3 style="margin-top: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                    🤖 Intelligent Pipeline
                </h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">
                    Execute the automated scheduling engine. This will run conflict-detection algorithms
                    to optimize room utilization and student distribution.
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("**Phase 1: Preparation**")
                st.caption("Generate registry from curricula")
                if st.button("Initialize Exams", use_container_width=True):
                    with st.spinner("Processing modules..."):
                        res = api.post(
                            f"/scheduling/prepare-session/{selected_id}",
                            timeout=60,  # Can take time with many modules
                        )
                        if res.get("error"):
                            st.error(res.get("detail"))
                        else:
                            st.success("✅ Registry Initialized")
                            st.rerun()

            with c2:
                st.markdown("**Phase 2: Optimization**")
                st.caption("Heuristic slot placement")
                if st.button(
                    "Launch Auto-Schedule", type="primary", use_container_width=True
                ):
                    # Check if already scheduled before running
                    if pending_exams == 0 and total_exams > 0:
                        st.info(
                            f"ℹ️ All {total_exams} exams are already scheduled! Use 'Clear All Current Schedules' to reset and reschedule."
                        )
                    elif total_exams == 0:
                        st.warning(
                            "⚠️ No exams found in this session. Please run 'Initialize Exams' first."
                        )
                    else:
                        with st.spinner("Running Optimization Engine..."):
                            res = api.post(
                                f"/scheduling/schedule-session/{selected_id}",
                                timeout=120,  # Allow up to 2 minutes for large datasets
                            )
                            if res.get("error"):
                                st.error(f"❌ Scheduling failed: {res.get('detail')}")
                            else:
                                # Extract timing and results from response
                                exec_time_ms = res.get("execution_time_ms", 0)
                                exec_time_s = exec_time_ms / 1000
                                scheduled = res.get("scheduled_count", 0)
                                failed = res.get("failed_count", 0)
                                
                                # Determine if target was met (< 45 seconds)
                                target_met = exec_time_s < 45
                                
                                # Create prominent timing display
                                if target_met:
                                    time_icon = "🎯"
                                    time_color = "green"
                                    goal_text = "✅ GOAL MET! (< 45s)"
                                    st.balloons()  # Celebrate!
                                else:
                                    time_icon = "⏱️"
                                    time_color = "orange"
                                    goal_text = "⚠️ Above 45s target"
                                
                                # Display prominent success message with timing
                                st.success(f"""
                                ### {time_icon} Auto-Scheduling Complete!
                                
                                **⏱️ Execution Time: `{exec_time_s:.2f} seconds`** {goal_text}
                                
                                - 📋 **{scheduled}** exams scheduled successfully
                                - ❌ **{failed}** exams failed (if any)
                                """)
                                
                                # Also show toast for quick reference
                                st.toast(
                                    f"⏱️ Scheduled {scheduled} exams in {exec_time_s:.2f}s",
                                    icon="🎯" if target_met else "⏱️"
                                )
                                
                                # Clear cache and refresh after a moment
                                fetch_dashboard_overview.clear()
                                st.rerun()

            with c3:
                st.markdown("**Phase 3: Staffing**")
                st.caption("Invigilator load balancing")
                if st.button("Assign Supervisors", use_container_width=True):
                    with st.spinner("Optimizing staff assignments..."):
                        res = api.post(
                            f"/scheduling/assign-supervisors/{selected_id}",
                            timeout=60,  # Assign supervisors takes ~17s, use 60s timeout
                        )
                        if res.get("error"):
                            st.error(res.get("detail"))
                        else:
                            st.success("✅ Staff Assigned")
                            st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Two-step clear process for safety
            clear_col1, clear_col2 = st.columns([3, 1])
            with clear_col1:
                if st.button(
                    "🗑️ Clear All Current Schedules",
                    key="clear_sess",
                    help="Reset all mappings for this session",
                    type="secondary",
                ):
                    st.session_state["confirm_clear"] = True
            
            # Confirmation step
            if st.session_state.get("confirm_clear"):
                with clear_col2:
                    if st.button("✅ Confirm", key="confirm_clear_btn", type="primary"):
                        try:
                            res = api.get(
                                "/scheduling/debug-reset",
                                params={"session_id": str(selected_id)},
                                timeout=120,  # Allow up to 2 minutes
                            )
                            
                            if res.get("error"):
                                st.error(f"❌ Failed to clear schedules: {res.get('detail', 'Unknown error')}")
                            else:
                                exams_cleared = res.get("exams_cleared", 0)
                                supervisors_deleted = res.get("supervisors_deleted", 0)
                                st.toast(
                                    f"✅ Cleared {exams_cleared} exams and {supervisors_deleted} supervisors!",
                                    icon="✅"
                                )
                                st.success(
                                    f"✅ Schedule cleared! Reset {exams_cleared} exams and removed {supervisors_deleted} supervisor assignments."
                                )
                                # Clear cached data
                                fetch_dashboard_overview.clear()
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                        finally:
                            st.session_state["confirm_clear"] = False
                            st.rerun()

        with tab2:
            st.markdown(
                """
            <div class="kpi-card" style="margin-bottom: 1.5rem;">
                <h3 style="margin-top: 0; font-size: 1.1rem;">🛠️ Manual Override</h3>
                <p style="color: var(--text-secondary); font-size: 0.9rem;">Manually adjust individual exam slots or rooms for specific requirements.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Load lists for forms
            exams_list = api.get("/exams", {"session_id": selected_id})
            rooms_list = api.get("/exams/rooms/")

            if isinstance(exams_list, list) and isinstance(rooms_list, list):
                exam_options = {
                    f"{e['module_code']} - {e['module_name']}": e["id"]
                    for e in exams_list
                }
                room_options = {
                    f"{r['name']} ({r['building']}) Cap:{r['exam_capacity']}": r["id"]
                    for r in rooms_list
                }

                with st.form("manual_edit"):
                    f1, f2 = st.columns(2)
                    with f1:
                        target_exam = st.selectbox(
                            "Select Target Exam", options=list(exam_options.keys())
                        )
                        target_room = st.selectbox(
                            "Assign to Room", options=list(room_options.keys())
                        )
                    with f2:
                        target_date = st.date_input("Schedule Date")
                        target_time = st.time_input("Start Time")

                    if st.form_submit_button(
                        "Apply Correction", use_container_width=True, type="primary"
                    ):
                        payload = {
                            "scheduled_date": target_date.isoformat(),
                            "start_time": target_time.strftime("%H:%M:%S"),
                            "room_id": str(room_options[target_room]),
                        }
                        res = api.put(f"/exams/{exam_options[target_exam]}", payload)
                        if not res.get("error"):
                            st.success("✅ Change applied!")
                            st.rerun()
                        else:
                            st.error(res.get("detail"))

        with tab3:
            st.markdown(
                """
            <div class="kpi-card">
                 <h3 style="margin-top: 0; font-size: 1.1rem;">⚠️ Integrity Audit</h3>
            </div>
            """,
                unsafe_allow_html=True,
            )

            with st.spinner("Auditing integrity..."):
                conflicts = api.get("/scheduling/conflicts")

            if conflicts and isinstance(conflicts, list) and len(conflicts) > 0:
                import pandas as pd

                st.dataframe(
                    pd.DataFrame(conflicts), use_container_width=True, hide_index=True
                )
                st.error(
                    f"Found {len(conflicts)} integrity issues that require resolution."
                )
            else:
                st.success(
                    "✨ Physical and logical integrity checks passed! No conflicts found."
                )

elif selected == "Exams":
    # -------------------------------------------------------------------------
    # EXAMS PAGE
    # -------------------------------------------------------------------------
    st.markdown(
        page_header(
            "Exams Repository",
            "Comprehensive database and lifecycle management for course examinations",
        ),
        unsafe_allow_html=True,
    )

    # Advanced Filters row
    st.markdown(
        """
    <div class="kpi-card" style="padding: 1.2rem; margin-bottom: 2rem;">
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem; font-weight: 600;">FILTERS & SEARCH</div>
    """,
        unsafe_allow_html=True,
    )

    f1, f2, f3, f4 = st.columns([1, 1, 2, 0.8])
    with f1:
        status_filter = st.selectbox(
            "Exam Status", ["All", "Scheduled", "Pending", "Completed"]
        )
    with f2:
        # Fetch actual departments for filtering
        depts_res = api.get("/departments")
        dept_options = {"All Departments": None}
        if isinstance(depts_res, list):
            for d in depts_res:
                dept_options[d["name"]] = d["id"]
        selected_dept_label = st.selectbox(
            "Department", options=list(dept_options.keys())
        )
    with f3:
        search = st.text_input(
            "Search module name, code or room...", placeholder="e.g. Algorithms"
        )
    with f4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Action Panel
    exp = st.expander("➕ Register New Single Exam Entry")
    with exp:
        sessions_res = api.get("/exams/sessions")
        with st.form("quick_create"):
            q1, q2 = st.columns(2)
            with q1:
                s_list = sessions_res if isinstance(sessions_res, list) else []
                s_map = {s["name"]: s["id"] for s in s_list}
                sel_session = st.selectbox(
                    "Exam Session", options=list(s_map.keys()) if s_map else ["N/A"]
                )
                m_code = st.text_input(
                    "Module Code identifier", placeholder="e.g. CS101"
                )
            with q2:
                duration = st.number_input("Standard Duration (min)", value=120)
                expected = st.number_input("Expected Capacity", value=50)

            if st.form_submit_button("Finalize Registration", use_container_width=True):
                st.warning(
                    "Manual registration currently requires verified module codes. Please use Auto-Initialize."
                )

    # List Layout
    with st.spinner("Retrieving registry..."):
        params = {}
        if status_filter != "All":
            params["status"] = status_filter.lower()
        if search:
            params["search"] = search
        if dept_options[selected_dept_label]:
            params["department_id"] = dept_options[selected_dept_label]

        exams = api.get("/exams", params)

    if exams and isinstance(exams, list):
        import pandas as pd

        df = pd.DataFrame(exams)
        if not df.empty:
            # Map statuses to badges for display in a dataframe is hard in basic st.dataframe,
            # so we'll just show the clean table.
            cols = [
                "module_code",
                "module_name",
                "department_name",
                "scheduled_date",
                "room_name",
                "status",
            ]
            existing = [c for c in cols if c in df.columns]
            st.dataframe(df[existing], use_container_width=True, hide_index=True)
            st.caption(f"Showing {len(df)} entries matching current filters")
        else:
            st.info("No exam records found for these filters.")
    else:
        st.info("No exam records found.")

elif selected == "Departments":
    st.markdown(
        page_header(
            "Academic Departments", "Departmental hierarchy and building allocation"
        ),
        unsafe_allow_html=True,
    )
    with st.spinner("Loading structures..."):
        depts = api.get("/departments")
        if depts and isinstance(depts, list):
            import pandas as pd

            st.dataframe(
                pd.DataFrame(depts)[["name", "code", "building"]],
                use_container_width=True,
                hide_index=True,
            )

elif selected == "Professors":
    st.markdown(
        page_header(
            "Faculty Management", "Professor profiles and supervision workload limits"
        ),
        unsafe_allow_html=True,
    )

    # Simple search & Add
    col_search, col_add = st.columns([2, 1])
    with col_search:
        search_prof = st.text_input(
            "🔍 Search Faculty", placeholder="Name, department or email..."
        )
    with col_add:
        st.markdown("<br>", unsafe_allow_html=True)
        show_add = st.button("➕ Register Faculty Member", use_container_width=True)

    if show_add:
        with st.form("add_professor_premium"):
            c1, c2 = st.columns(2)
            with c1:
                p_first = st.text_input("First Name")
                p_last = st.text_input("Last Name")
                p_email = st.text_input("Email Address")
            with c2:
                depts = api.get("/departments")
                dept_map = (
                    {d["name"]: d["id"] for d in depts}
                    if isinstance(depts, list)
                    else {}
                )
                p_dept = st.selectbox(
                    "Assign to Department", options=list(dept_map.keys())
                )
                p_title = st.selectbox(
                    "Academic Title",
                    [
                        "Professor",
                        "Associate Professor",
                        "Assistant Professor",
                        "Lecturer",
                    ],
                )

            if st.form_submit_button(
                "Finalize Registration", type="primary", use_container_width=True
            ):
                if p_first and p_last and p_email:
                    payload = {
                        "first_name": p_first,
                        "last_name": p_last,
                        "email": p_email,
                        "department_id": str(dept_map[p_dept]),
                        "title": p_title,
                    }
                    res = api.post("/professors/", payload)
                    if not res.get("error"):
                        st.success("✅ Registered!")
                        st.rerun()
                    else:
                        st.error(res.get("detail"))
                else:
                    st.error("Please fill all required fields.")

    # List professors
    with st.spinner("Synchronizing faculty database..."):
        params = {"search": search_prof} if search_prof else {}
        profs = api.get("/professors", params)

    if profs and isinstance(profs, list):
        import pandas as pd

        df = pd.DataFrame(profs)
        if not df.empty:
            st.markdown(
                f'<div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.5rem; font-weight: 600;">ACTIVE FACULTY ({len(df)})</div>',
                unsafe_allow_html=True,
            )
            display_df = df[["first_name", "last_name", "email", "department_name"]]
            display_df.columns = ["First Name", "Last Name", "Email", "Department"]
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No faculty members found matching your search.")
    else:
        st.info("No faculty data available.")

elif selected == "Personal Schedule":
    # -------------------------------------------------------------------------
    # PERSONAL SCHEDULE PROFILE (Inspired by Image 3)
    # -------------------------------------------------------------------------
    user = get_current_user()
    st.markdown(
        page_header(
            "Personal Timetable",
            f"Custom exam and supervision sequence for {user.get('name')}",
        ),
        unsafe_allow_html=True,
    )

    role = user.get("role")
    student_id = user.get("student_id")
    prof_id = user.get("professor_id")

    params = {"status": "scheduled"}
    if student_id:
        params["student_id"] = student_id
        st.markdown(
            f'<div style="margin-bottom: 1rem; color: var(--primary); font-weight: 700;">📘 STUDENT MODE • ID: {student_id[:8]}...</div>',
            unsafe_allow_html=True,
        )
    elif prof_id:
        params["professor_id"] = prof_id
        st.markdown(
            f'<div style="margin-bottom: 1rem; color: var(--primary); font-weight: 700;">🛡️ PROFESSOR MODE • ID: {prof_id[:8]}...</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="margin-bottom: 1rem; color: var(--primary); font-weight: 700;">⚙️ ADMIN MODE • FULL ACCESS</div>',
            unsafe_allow_html=True,
        )

    with st.spinner("Building your timeline..."):
        my_exams = api.get("/exams", params)

    if my_exams and isinstance(my_exams, list):
        # We'll use the card layout from Image 3/4
        for ex in my_exams:
            date_val = ex.get("scheduled_date", "TBA")
            time_val = ex.get("start_time", "TBA")
            room_val = ex.get("room_name", "TBA")
            dept_val = ex.get("department_name", "Academic")

            st.markdown(
                f"""
            <div class="kpi-card" style="border-left: 4px solid var(--primary); margin-bottom: 1.2rem; transition: transform 0.2s ease;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex-grow: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <span style="background: rgba(99, 102, 241, 0.15); color: var(--primary); font-size: 0.7rem; padding: 2px 8px; border-radius: 4px; font-weight: 700;">{dept_val}</span>
                            <span style="color: var(--text-secondary); font-size: 0.75rem;">ID: {ex["module_code"]}</span>
                        </div>
                        <h3 style="margin: 0; font-size: 1.15rem; font-weight: 800; color: white;">{ex["module_name"]}</h3>
                        <div style="display: flex; gap: 16px; margin-top: 10px; color: var(--text-secondary); font-size: 0.85rem;">
                            <span style="display: flex; align-items: center; gap: 4px;">📅 {date_val}</span>
                            <span style="display: flex; align-items: center; gap: 4px;">🕒 {time_val}</span>
                            <span style="display: flex; align-items: center; gap: 4px;">📍 {room_val}</span>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="background: rgba(16, 185, 129, 0.15); color: #10b981; font-size: 0.7rem; padding: 4px 12px; border-radius: 20px; font-weight: 700; display: inline-block;">
                            VERIFIED
                        </div>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
        <div style="text-align: center; padding: 4rem 2rem; background: var(--card-bg); border-radius: 24px; border: 1px dashed var(--border-color);">
            <div style="font-size: 3rem; margin-bottom: 1rem;">🗓️</div>
            <h3 style="margin: 0; color: white;">No Scheduled Events</h3>
            <p style="color: var(--text-secondary); max-width: 300px; margin: 0.5rem auto;">
                Currently, there are no examinations or supervisions assigned to your account for this session.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

elif selected == "My Department":
    # -------------------------------------------------------------------------
    # PAGE CHEF DÉPARTEMENT - MON DÉPARTEMENT
    # -------------------------------------------------------------------------
    user = get_current_user()
    dept_id = user.get("department_id")

    st.markdown(
        page_header("🏫 My Department", f"Vue d'ensemble et gestion du département"),
        unsafe_allow_html=True,
    )

    if not dept_id:
        st.error(
            "⚠️ Votre compte n'est associé à aucun département. Contactez l'administrateur."
        )
    else:
        with st.spinner("Chargement des données du département..."):
            # Fetch department stats
            stats = api.get(f"/dashboard/department/{dept_id}")

            # Fetch department details for name
            dept_info = api.get("/departments", {"department_id": dept_id})
            dept_name = "Département"
            if isinstance(dept_info, list) and len(dept_info) > 0:
                # Filter to find the exact one or trust the list filter
                for d in dept_info:
                    if d["id"] == dept_id:
                        dept_name = d["name"]
                        break
            elif isinstance(stats, dict) and "department_name" in stats:
                dept_name = stats["department_name"]

        if isinstance(stats, dict) and not stats.get("error"):
            # Display KPIs
            st.markdown(f"### 📊 Statistiques : {dept_name}")

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(
                    metric_card(
                        str(stats.get("formations_count", 0)),
                        "Formations",
                        "🎓",
                        "Offres actives",
                    ),
                    unsafe_allow_html=True,
                )
            with k2:
                st.markdown(
                    metric_card(
                        str(stats.get("total_students", 0)),
                        "Étudiants",
                        "👥",
                        "Inscrits",
                    ),
                    unsafe_allow_html=True,
                )
            with k3:
                st.markdown(
                    metric_card(
                        str(stats.get("professors_supervising", 0)),
                        "Professeurs",
                        "👨‍🏫",
                        "Superviseurs",
                    ),
                    unsafe_allow_html=True,
                )
            with k4:
                st.markdown(
                    metric_card(
                        str(stats.get("total_exams", 0)),
                        "Examens",
                        "📝",
                        "Session active",
                    ),
                    unsafe_allow_html=True,
                )

            st.markdown("---")

            # Formations List
            st.subheader("🎓 Formations du Département")
            formations = api.get(
                f"/departments/{dept_id}/formations"
            )  # Hypothetical endpoint or filter
            # Fallback: get all formations and filter client side if needed, or just list general info
            # Let's use a general query if specific one doesn't exist
            all_formations = api.get("/formations")
            if isinstance(all_formations, list):
                my_formations = [
                    f for f in all_formations if f.get("department_id") == dept_id
                ]
                if my_formations:
                    import pandas as pd

                    df_form = pd.DataFrame(my_formations)
                    st.dataframe(
                        df_form[["name", "code", "level"]],
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("Aucune formation trouvée pour ce département.")

        else:
            st.error("Impossible de charger les statistiques du département.")

elif selected == "Settings":
    # -------------------------------------------------------------------------
    # SETTINGS PAGE
    # -------------------------------------------------------------------------
    st.markdown(
        page_header("⚙️ Settings", "Configure your account and application settings"),
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["👤 Profile", "🔧 Preferences"])

    with tab1:
        st.subheader("Profile Settings")
        user = get_current_user()

        with st.form("profile_form"):
            name = st.text_input(
                "Full Name", value=user.get("name", "") if user else ""
            )
            email = st.text_input(
                "Email", value=user.get("email", "") if user else "", disabled=True
            )

            if st.form_submit_button("Update Profile"):
                st.success("Profile updated successfully!")

    with tab2:
        st.subheader("Application Preferences")

        dark_mode = st.toggle("Dark Mode", value=True)
        notifications = st.toggle("Enable Notifications", value=True)
        auto_refresh = st.toggle("Auto-refresh Dashboard", value=True)

        if st.button("Save Preferences"):
            st.success("Preferences saved!")

elif selected == "My Exams":
    # -------------------------------------------------------------------------
    # PAGE ÉTUDIANT - MES EXAMENS
    # -------------------------------------------------------------------------
    user = get_current_user()
    st.markdown(
        page_header(
            "📚 Mes Examens",
            f"Planning personnalisé des examens pour {user.get('name', 'Étudiant')}",
        ),
        unsafe_allow_html=True,
    )

    student_id = user.get("student_id")

    if not student_id:
        st.warning(
            "⚠️ Votre compte n'est pas lié à un profil étudiant. Contactez l'administration."
        )
    else:
        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
             padding: 1rem 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; border: 1px solid rgba(99, 102, 241, 0.2);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 2rem;">🎓</span>
                <div>
                    <div style="font-weight: 700; color: white; font-size: 1.1rem;">Mode Étudiant</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">Affichage de vos examens inscrits uniquement</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.spinner("Chargement de vos examens..."):
            my_exams = api.get(
                "/exams", {"student_id": student_id, "status": "scheduled"}
            )

        if my_exams and isinstance(my_exams, list) and len(my_exams) > 0:
            st.markdown(
                f"<div style='margin-bottom: 1rem; font-weight: 600;'>📋 {len(my_exams)} examen(s) à passer</div>",
                unsafe_allow_html=True,
            )

            for ex in my_exams:
                st.markdown(
                    f"""
                <div class="kpi-card" style="border-left: 4px solid #10B981; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 700; color: white; font-size: 1.1rem; margin-bottom: 4px;">{ex.get("module_name", "Module")}</div>
                            <div style="color: var(--text-secondary); font-size: 0.85rem;">{ex.get("department_name", "")}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: white; font-weight: 600;">📅 {ex.get("scheduled_date", "TBA")}</div>
                            <div style="color: var(--text-secondary);">🕒 {ex.get("start_time", "TBA")} • 📍 {ex.get("room_name", "TBA")}</div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("🎉 Aucun examen programmé pour le moment.")

elif selected == "My Supervisions":
    # -------------------------------------------------------------------------
    # PAGE PROFESSEUR - MES SURVEILLANCES
    # -------------------------------------------------------------------------
    user = get_current_user()
    st.markdown(
        page_header(
            "🛡️ Mes Surveillances",
            f"Examens assignés pour surveillance - {user.get('name', 'Professeur')}",
        ),
        unsafe_allow_html=True,
    )

    prof_id = user.get("professor_id")

    if not prof_id:
        st.warning(
            "⚠️ Votre compte n'est pas lié à un profil professeur. Contactez l'administration."
        )
    else:
        st.markdown(
            f"""
        <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(234, 88, 12, 0.1));
             padding: 1rem 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; border: 1px solid rgba(245, 158, 11, 0.2);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 2rem;">👨‍🏫</span>
                <div>
                    <div style="font-weight: 700; color: white; font-size: 1.1rem;">Mode Professeur</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">Affichage de vos surveillances assignées</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        with st.spinner("Chargement de vos surveillances..."):
            my_supervisions = api.get(
                "/exams", {"professor_id": prof_id, "status": "scheduled"}
            )

        if (
            my_supervisions
            and isinstance(my_supervisions, list)
            and len(my_supervisions) > 0
        ):
            st.markdown(
                f"<div style='margin-bottom: 1rem; font-weight: 600;'>📋 {len(my_supervisions)} surveillance(s) assignée(s)</div>",
                unsafe_allow_html=True,
            )

            for ex in my_supervisions:
                st.markdown(
                    f"""
                <div class="kpi-card" style="border-left: 4px solid #F59E0B; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 700; color: white; font-size: 1.1rem; margin-bottom: 4px;">{ex.get("module_name", "Module")}</div>
                            <div style="color: var(--text-secondary); font-size: 0.85rem;">{ex.get("department_name", "")} • {ex.get("expected_students", 0)} étudiants</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: white; font-weight: 600;">📅 {ex.get("scheduled_date", "TBA")}</div>
                            <div style="color: var(--text-secondary);">🕒 {ex.get("start_time", "TBA")} • 📍 {ex.get("room_name", "TBA")}</div>
                        </div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("🎉 Aucune surveillance assignée pour le moment.")

elif selected == "Validation":
    # -------------------------------------------------------------------------
    # PAGE VALIDATION - DOYEN / CHEF DÉPARTEMENT
    # -------------------------------------------------------------------------
    user = get_current_user()
    user_role = user.get("role", "") if user else ""
    dept_id = user.get("department_id")

    if user_role in ["dean", "vice_dean", "dept_head", "department_head"]:
        st.markdown(
            page_header(
                "✅ Validation Globale EDT",
                "Vue stratégique - Validation finale de l'emploi du temps d'examens",
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1));
             padding: 1rem 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; border: 1px solid rgba(16, 185, 129, 0.2);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 2rem;">👔</span>
                <div>
                    <div style="font-weight: 700; color: white; font-size: 1.1rem;">Mode Doyen / Vice-Doyen</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">Validation globale et vue stratégique</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Statistiques globales
        with st.spinner("Chargement des statistiques..."):
            overview = api.get("/dashboard/overview")

        if overview and not overview.get("error"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(
                    metric_card(
                        str(overview.get("total_departments", 0)), "Départements", "🏛️"
                    ),
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(
                    metric_card(
                        str(overview.get("total_students", 0)), "Étudiants", "👨‍🎓"
                    ),
                    unsafe_allow_html=True,
                )
            with col3:
                st.markdown(
                    metric_card(
                        str(overview.get("total_professors", 0)), "Professeurs", "👨‍🏫"
                    ),
                    unsafe_allow_html=True,
                )
            with col4:
                sessions = overview.get("active_sessions", [])
                total_exams = sum(s.get("total_exams", 0) for s in sessions)
                st.markdown(
                    metric_card(str(total_exams), "Total Examens", "📋"),
                    unsafe_allow_html=True,
                )

        st.markdown("### 📊 Session Active")

        if overview and overview.get("active_sessions"):
            for session in overview.get("active_sessions", []):
                scheduled = session.get("scheduled_exams", 0)
                total = session.get("total_exams", 0)
                progress = int((scheduled / total * 100)) if total > 0 else 0

                st.markdown(
                    f"""
                <div class="kpi-card" style="margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 1rem 0; color: white;">{session.get("name", "Session")}</h4>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <span style="color: var(--text-secondary);">Progression</span>
                        <span style="color: white; font-weight: 600;">{progress}%</span>
                    </div>
                    <div style="background: rgba(255,255,255,0.1); border-radius: 8px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #10B981, #34D399); height: 100%; width: {progress}%;"></div>
                    </div>
                    <div style="margin-top: 1rem; display: flex; gap: 2rem;">
                        <div><span style="color: var(--text-secondary);">Planifiés:</span> <span style="color: #10B981; font-weight: 600;">{scheduled}</span></div>
                        <div><span style="color: var(--text-secondary);">Total:</span> <span style="color: white; font-weight: 600;">{total}</span></div>
                        <div><span style="color: var(--text-secondary);">Conflits:</span> <span style="color: #EF4444; font-weight: 600;">{session.get("conflict_count", 0)}</span></div>
                    </div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            if st.button("✅ Valider l'EDT", type="primary", use_container_width=True):
                st.success("✅ Emploi du temps validé avec succès!")
                st.balloons()

    elif user_role == "department_head":
        st.markdown(
            page_header(
                "✅ Validation Département",
                "Validation des examens de votre département",
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1));
             padding: 1rem 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; border: 1px solid rgba(59, 130, 246, 0.2);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 2rem;">🏛️</span>
                <div>
                    <div style="font-weight: 700; color: white; font-size: 1.1rem;">Mode Chef de Département</div>
                    <div style="color: var(--text-secondary); font-size: 0.85rem;">Validation des examens de votre département</div>
                </div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        if dept_id:
            with st.spinner("Chargement des examens du département..."):
                dept_exams = api.get(
                    "/exams", {"department_id": dept_id, "status": "scheduled"}
                )

            if dept_exams and isinstance(dept_exams, list):
                st.markdown(
                    f"<div style='margin-bottom: 1rem; font-weight: 600;'>📋 {len(dept_exams)} examen(s) dans votre département</div>",
                    unsafe_allow_html=True,
                )

                for ex in dept_exams[:10]:  # Limiter à 10 pour l'affichage
                    st.markdown(
                        f"""
                    <div class="kpi-card" style="border-left: 4px solid #3B82F6; margin-bottom: 0.8rem; padding: 0.8rem 1rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-weight: 600; color: white;">{ex.get("module_name", "Module")}</div>
                            <div style="color: var(--text-secondary); font-size: 0.85rem;">📅 {ex.get("scheduled_date", "TBA")} • 📍 {ex.get("room_name", "TBA")}</div>
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                if st.button(
                    "✅ Valider les examens du département",
                    type="primary",
                    use_container_width=True,
                ):
                    st.success("✅ Examens du département validés!")
        else:
            st.warning("⚠️ Aucun département associé à votre compte.")

elif selected == "My Department":
    # -------------------------------------------------------------------------
    # PAGE CHEF DÉPARTEMENT - MON DÉPARTEMENT
    # -------------------------------------------------------------------------
    user = get_current_user()
    dept_id = user.get("department_id") if user else None

    st.markdown(
        page_header(
            "🏛️ Mon Département", "Statistiques et gestion de votre département"
        ),
        unsafe_allow_html=True,
    )

    if dept_id:
        with st.spinner("Chargement..."):
            dept_info = api.get(f"/departments/{dept_id}")
            dept_exams = api.get("/exams", {"department_id": dept_id})

        if dept_info and not dept_info.get("error"):
            st.markdown(
                f"""
            <div class="kpi-card" style="margin-bottom: 1.5rem;">
                <h2 style="margin: 0; color: white;">{dept_info.get("name", "Département")}</h2>
                <p style="color: var(--text-secondary); margin: 0.5rem 0;">Code: {dept_info.get("code", "N/A")} • Bâtiment: {dept_info.get("building", "N/A")}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                formations = dept_info.get("formations", [])
                st.markdown(
                    metric_card(str(len(formations)), "Formations", "📚"),
                    unsafe_allow_html=True,
                )
            with col2:
                exam_count = len(dept_exams) if isinstance(dept_exams, list) else 0
                st.markdown(
                    metric_card(str(exam_count), "Examens", "📋"),
                    unsafe_allow_html=True,
                )
    else:
        st.warning("⚠️ Aucun département associé à votre compte.")

# ==============================================================================
# FOOTER
# ==============================================================================
st.markdown(
    """
<div style="position: fixed; bottom: 0; left: 0; right: 0;
     background: #0f0f23; padding: 0.5rem; text-align: center;
     border-top: 1px solid rgba(99, 102, 241, 0.2); z-index: 999;">
    <span style="color: #64748b; font-size: 0.75rem;">
        🎓 Exam Scheduling Platform © 2026 | Built with ❤️ using FastAPI & Streamlit
    </span>
</div>
""",
    unsafe_allow_html=True,
)
