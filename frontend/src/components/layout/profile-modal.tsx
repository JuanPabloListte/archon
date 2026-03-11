"use client"

import { useState, useEffect } from "react"
import { X, User, Lock, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { useI18n } from "@/lib/i18n"

export function ProfileModal({ onClose }: { onClose: () => void }) {
  const { t } = useI18n()
  const [email, setEmail] = useState("")
  const [memberSince, setMemberSince] = useState("")
  const [emailSuccess, setEmailSuccess] = useState(false)
  const [emailError, setEmailError] = useState("")
  const [savingEmail, setSavingEmail] = useState(false)
  const [currentPw, setCurrentPw] = useState("")
  const [newPw, setNewPw] = useState("")
  const [pwSuccess, setPwSuccess] = useState(false)
  const [pwError, setPwError] = useState("")
  const [savingPw, setSavingPw] = useState(false)

  useEffect(() => {
    api.users.me().then(u => {
      setEmail(u.email)
      setMemberSince(new Date(u.created_at).toLocaleDateString())
    })
  }, [])

  async function saveEmail(e: React.FormEvent) {
    e.preventDefault()
    setSavingEmail(true); setEmailError(""); setEmailSuccess(false)
    try { await api.users.updateMe(email); setEmailSuccess(true) }
    catch (err: unknown) { setEmailError(err instanceof Error ? err.message : "Failed") }
    finally { setSavingEmail(false) }
  }

  async function savePassword(e: React.FormEvent) {
    e.preventDefault()
    setSavingPw(true); setPwError(""); setPwSuccess(false)
    try { await api.users.changePassword(currentPw, newPw); setPwSuccess(true); setCurrentPw(""); setNewPw("") }
    catch (err: unknown) { setPwError(err instanceof Error ? err.message : "Failed") }
    finally { setSavingPw(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-surface border bd1 rounded-2xl w-full max-w-md mx-4 shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b bd1">
          <h2 className="t1 font-semibold text-lg">{t("myProfile")}</h2>
          <button onClick={onClose} className="t3 hover-t1 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-6">
          {memberSince && <p className="t4 text-xs">{t("memberSince")}: {memberSince}</p>}

          <form onSubmit={saveEmail} className="space-y-3">
            <div className="flex items-center gap-2 t2 text-sm font-medium">
              <User className="w-4 h-4 text-archon-400" /> {t("email")}
            </div>
            <Input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
            {emailError && <p className="text-red-500 text-xs">{emailError}</p>}
            {emailSuccess && <p className="text-green-500 text-xs flex items-center gap-1"><CheckCircle className="w-3 h-3" /> {t("emailUpdated")}</p>}
            <Button type="submit" size="sm" loading={savingEmail}>{t("saveEmail")}</Button>
          </form>

          <div className="border-t bd1" />

          <form onSubmit={savePassword} className="space-y-3">
            <div className="flex items-center gap-2 t2 text-sm font-medium">
              <Lock className="w-4 h-4 text-archon-400" /> {t("changePassword")}
            </div>
            <div className="space-y-2">
              <Label>{t("currentPassword")}</Label>
              <Input type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} required />
            </div>
            <div className="space-y-2">
              <Label>{t("newPassword")}</Label>
              <Input type="password" value={newPw} onChange={e => setNewPw(e.target.value)} required minLength={8} />
            </div>
            {pwError && <p className="text-red-500 text-xs">{pwError}</p>}
            {pwSuccess && <p className="text-green-500 text-xs flex items-center gap-1"><CheckCircle className="w-3 h-3" /> {t("passwordChanged")}</p>}
            <Button type="submit" size="sm" loading={savingPw}>{t("savePassword")}</Button>
          </form>
        </div>
      </div>
    </div>
  )
}
