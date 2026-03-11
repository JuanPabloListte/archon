"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from "react"

export type Locale = "en" | "es"

const translations = {
  en: {
    // Nav
    dashboard: "Dashboard",
    projects: "Projects",
    // Profile menu
    profile: "Profile",
    preferences: "Preferences",
    theme: "Theme",
    language: "Language",
    signOut: "Sign out",
    // Profile modal
    myProfile: "My Profile",
    email: "Email",
    memberSince: "Member since",
    changePassword: "Change Password",
    currentPassword: "Current password",
    newPassword: "New password (min. 8 chars)",
    saveEmail: "Save email",
    savePassword: "Save password",
    cancel: "Cancel",
    saving: "Saving...",
    emailUpdated: "Email updated successfully",
    passwordChanged: "Password changed successfully",
    // Themes
    themeDark: "Dark",
    themeLight: "Light",
    themeSystem: "System",
    close: "Close",
    // Auth
    signInTitle: "Sign in to Archon",
    aiSystemAuditor: "AI System Auditor",
    createAccount: "Create account",
    startAuditing: "Start auditing your systems",
    password: "Password",
    passwordPlaceholder: "••••••••",
    minCharsPlaceholder: "Min. 8 characters",
    signIn: "Sign in",
    noAccount: "No account?",
    register: "Register",
    alreadyAccount: "Already have an account?",
    // Dashboard
    dashboardSubtitle: "Overview of your audited systems",
    totalProjects: "Total Projects",
    projectsAudited: "Projects Audited",
    totalFindings: "Total Findings",
    healthAvg: "Health Avg",
    recentProjects: "Recent Projects",
    noProjectsYet: "No projects yet.",
    createFirstProjectLink: "Create your first project →",
    // Projects page
    projectsSubtitle: "Manage your audited systems",
    newProject: "New Project",
    createNewProject: "Create New Project",
    projectName: "Project Name",
    projectNamePlaceholder: "My API Service",
    descriptionOptional: "Description (optional)",
    descriptionPlaceholder: "Describe the system...",
    create: "Create",
    open: "Open",
    deleteProjectConfirm: "Delete this project? This cannot be undone.",
    createFirstProjectBtn: "Create your first project",
    // Project detail
    runAudit: "Run Audit",
    healthScore: "Health Score",
    connections: "Connections",
    aiSummary: "AI Summary",
    quickActions: "Quick Actions",
    viewFindings: "View Findings",
    allDetectedIssues: "All detected issues",
    technicalReport: "Technical Report",
    fullAuditReport: "Full audit report",
    aiChat: "AI Chat",
    queryAnalyzedSystem: "Query the analyzed system",
    noConnections: "No connections. Add an OpenAPI spec or database.",
    openApiLabel: "OpenAPI URL",
    connectionStringLabel: "Connection String",
    addIngest: "Add & Ingest",
    deleteConnection: "Delete this connection?",
    auditComplete: "Audit complete",
    findings: "findings",
    runningAudit: "Running audit...",
    auditFailed: "Audit failed",
    dismiss: "Dismiss",
    clearingFindings: "Clearing previous findings...",
    savingFindings: "Saving findings...",
    generatingReport: "Generating report...",
    indexingEmbeddings: "Indexing embeddings for RAG...",
    processing: "Processing...",
    summary: "Summary",
    // Findings page
    auditFindings: "Audit Findings",
    issuesDetected: "issues detected",
    backToProject: "Back to project",
    noFindingsYet: "No findings yet. Run an audit first.",
    noFindingsFilter: "No findings match the filter.",
    recommendation: "Recommendation",
    // Report page
    generated: "Generated",
    endpoints: "Endpoints",
    dbTables: "DB Tables",
    totalIssues: "Total Issues",
    executiveSummary: "Executive Summary",
    issuesBySeverity: "Issues by Severity",
    allFindings: "All Findings",
    noReportFound: "No report found. Run an audit to generate one.",
    fix: "Fix:",
    // Chat page
    aiChatSubtitle: "Ask questions about the analyzed system",
    suggestedQuestions: "Suggested questions",
    aboutArchonAI: "About Archon AI",
    aboutArchonAIDesc: "Archon uses RAG (Retrieval-Augmented Generation) to answer questions using the actual data analyzed from your system. Powered by a local LLM via Ollama.",
    chatPlaceholder: "Ask about endpoints, database, security findings...",
    chatWelcome: "Hello! I'm Archon. Ask me anything about the analyzed system — endpoints, tables, security findings, or recommendations.",
    enterToSend: "Press Enter to send, Shift+Enter for newline",
    thinkingProcess: "Thinking process",
    contextRetrieved: "Context retrieved:",
    showFullPrompt: "Show full prompt",
    hidePrompt: "Hide prompt",
    sq1: "Which endpoints don't have authentication?",
    sq2: "What are the most critical security issues?",
    sq3: "Which database tables are missing indexes?",
    sq4: "What are the top 3 things to fix immediately?",
    sq5: "Are there any sensitive data exposure issues?",
  },
  es: {
    // Nav
    dashboard: "Tablero",
    projects: "Proyectos",
    // Profile menu
    profile: "Perfil",
    preferences: "Preferencias",
    theme: "Tema",
    language: "Idioma",
    signOut: "Cerrar sesión",
    // Profile modal
    myProfile: "Mi Perfil",
    email: "Correo electrónico",
    memberSince: "Miembro desde",
    changePassword: "Cambiar Contraseña",
    currentPassword: "Contraseña actual",
    newPassword: "Nueva contraseña (mín. 8 chars)",
    saveEmail: "Guardar correo",
    savePassword: "Guardar contraseña",
    cancel: "Cancelar",
    saving: "Guardando...",
    emailUpdated: "Correo actualizado correctamente",
    passwordChanged: "Contraseña cambiada correctamente",
    // Themes
    themeDark: "Oscuro",
    themeLight: "Claro",
    themeSystem: "Sistema",
    close: "Cerrar",
    // Auth
    signInTitle: "Iniciar sesión en Archon",
    aiSystemAuditor: "Auditor de sistemas con IA",
    createAccount: "Crear cuenta",
    startAuditing: "Empieza a auditar tus sistemas",
    password: "Contraseña",
    passwordPlaceholder: "••••••••",
    minCharsPlaceholder: "Mín. 8 caracteres",
    signIn: "Iniciar sesión",
    noAccount: "¿Sin cuenta?",
    register: "Registrarse",
    alreadyAccount: "¿Ya tienes cuenta?",
    // Dashboard
    dashboardSubtitle: "Resumen de tus sistemas auditados",
    totalProjects: "Total Proyectos",
    projectsAudited: "Proyectos Auditados",
    totalFindings: "Total Hallazgos",
    healthAvg: "Salud Prom.",
    recentProjects: "Proyectos Recientes",
    noProjectsYet: "Sin proyectos aún.",
    createFirstProjectLink: "Crea tu primer proyecto →",
    // Projects page
    projectsSubtitle: "Gestiona tus sistemas auditados",
    newProject: "Nuevo Proyecto",
    createNewProject: "Crear Nuevo Proyecto",
    projectName: "Nombre del Proyecto",
    projectNamePlaceholder: "Mi Servicio de API",
    descriptionOptional: "Descripción (opcional)",
    descriptionPlaceholder: "Describe el sistema...",
    create: "Crear",
    open: "Abrir",
    deleteProjectConfirm: "¿Eliminar este proyecto? No se puede deshacer.",
    createFirstProjectBtn: "Crear primer proyecto",
    // Project detail
    runAudit: "Ejecutar Auditoría",
    healthScore: "Puntuación de Salud",
    connections: "Conexiones",
    aiSummary: "Resumen IA",
    quickActions: "Acciones Rápidas",
    viewFindings: "Ver Hallazgos",
    allDetectedIssues: "Todos los problemas detectados",
    technicalReport: "Reporte Técnico",
    fullAuditReport: "Reporte completo de auditoría",
    aiChat: "Chat IA",
    queryAnalyzedSystem: "Consultar el sistema analizado",
    noConnections: "Sin conexiones. Agrega un spec OpenAPI o base de datos.",
    openApiLabel: "URL de OpenAPI",
    connectionStringLabel: "Cadena de conexión",
    addIngest: "Agregar e Ingestar",
    deleteConnection: "¿Eliminar esta conexión?",
    auditComplete: "Auditoría completa",
    findings: "hallazgos",
    runningAudit: "Ejecutando auditoría...",
    auditFailed: "Auditoría fallida",
    dismiss: "Cerrar",
    clearingFindings: "Limpiando hallazgos anteriores...",
    savingFindings: "Guardando hallazgos...",
    generatingReport: "Generando reporte...",
    indexingEmbeddings: "Indexando embeddings para RAG...",
    processing: "Procesando...",
    summary: "Resumen",
    // Findings page
    auditFindings: "Hallazgos de Auditoría",
    issuesDetected: "problemas detectados",
    backToProject: "Volver al proyecto",
    noFindingsYet: "Sin hallazgos aún. Ejecuta una auditoría primero.",
    noFindingsFilter: "No hay hallazgos que coincidan con el filtro.",
    recommendation: "Recomendación",
    // Report page
    generated: "Generado",
    endpoints: "Endpoints",
    dbTables: "Tablas de BD",
    totalIssues: "Total de Problemas",
    executiveSummary: "Resumen Ejecutivo",
    issuesBySeverity: "Problemas por Severidad",
    allFindings: "Todos los Hallazgos",
    noReportFound: "Sin reporte. Ejecuta una auditoría para generar uno.",
    fix: "Corrección:",
    // Chat page
    aiChatSubtitle: "Haz preguntas sobre el sistema analizado",
    suggestedQuestions: "Preguntas sugeridas",
    aboutArchonAI: "Acerca de Archon IA",
    aboutArchonAIDesc: "Archon usa RAG (Generación con Recuperación) para responder preguntas con los datos reales analizados de tu sistema. Potenciado por un LLM local vía Ollama.",
    chatPlaceholder: "Pregunta sobre endpoints, base de datos, hallazgos de seguridad...",
    chatWelcome: "¡Hola! Soy Archon. Pregúntame sobre el sistema analizado — endpoints, tablas, hallazgos de seguridad o recomendaciones.",
    enterToSend: "Enter para enviar, Shift+Enter para nueva línea",
    thinkingProcess: "Proceso de razonamiento",
    contextRetrieved: "Contexto recuperado:",
    showFullPrompt: "Mostrar prompt completo",
    hidePrompt: "Ocultar prompt",
    sq1: "¿Qué endpoints no tienen autenticación?",
    sq2: "¿Cuáles son los problemas de seguridad más críticos?",
    sq3: "¿Qué tablas de la base de datos no tienen índices?",
    sq4: "¿Cuáles son las 3 cosas más urgentes a corregir?",
    sq5: "¿Hay problemas de exposición de datos sensibles?",
  },
}

export type TranslationKey = keyof typeof translations.en

interface I18nContextValue {
  locale: Locale
  setLocale: (l: Locale) => void
  t: (key: TranslationKey) => string
}

const I18nContext = createContext<I18nContextValue | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en")

  useEffect(() => {
    const saved = localStorage.getItem("archon_locale") as Locale | null
    if (saved === "en" || saved === "es") setLocaleState(saved)
  }, [])

  function setLocale(l: Locale) {
    setLocaleState(l)
    localStorage.setItem("archon_locale", l)
  }

  function t(key: TranslationKey): string {
    return translations[locale][key] ?? translations.en[key] ?? key
  }

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>
}

export function useI18n() {
  const ctx = useContext(I18nContext)
  if (!ctx) throw new Error("useI18n must be used within I18nProvider")
  return ctx
}
