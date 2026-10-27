import React, { useState, useEffect, useRef } from "react";
import {
  Building2,
  MessageSquare,
  AlertTriangle,
  ShieldCheck,
  LogIn,
  LogOut,
  Bell,
  Send,
  UserPlus,
  MapPin,
  CheckCircle,
  Clock,
  FileText,
  Bot,
  X,
  Sparkles,
  Filter,
  Search,
  Navigation,
  Download,
  RotateCcw,
} from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const apiUrl = (path) => `${API_BASE_URL}${path}`;
const apiFetch = (path, options) => fetch(apiUrl(path), options);

// Fix leaflet default icon
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Warna pin per dinas
const formatDate = (value, options = {}) => {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("id-ID", options);
};

const renderChatText = (text) => {
  const blocks = String(text || "").split(/\n{2,}/);
  return blocks.map((block, index) => {
    const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
    const isList = lines.length > 1 && lines.every((line) => /^([-*•]|\d+[.)])\s+/.test(line));
    if (isList) {
      const ordered = lines.every((line) => /^\d+[.)]\s+/.test(line));
      const Tag = ordered ? "ol" : "ul";
      return (
        <Tag key={index} className="chat-list">
          {lines.map((line, lineIndex) => (
            <li key={lineIndex}>{line.replace(/^([-*•]|\d+[.)])\s+/, "")}</li>
          ))}
        </Tag>
      );
    }
    return <p key={index}>{block}</p>;
  });
};

const DEPT_COLORS = [
  "#ef4444", "#f97316", "#eab308", "#22c55e",
  "#14b8a6", "#3b82f6", "#8b5cf6", "#ec4899"
];
const createReportIcon = (color) =>
  L.divIcon({
    className: "report-map-marker",
    html: `
      <div style="--marker-color:${color}" aria-label="Laporan">
        <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          <path d="M14 2v6h6M8 13h8M8 17h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>`,
    iconSize: [32, 40],
    iconAnchor: [16, 40],
    popupAnchor: [0, -38],
  });

// Komponen untuk re-center peta
function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => { map.setView(center, map.getZoom()); }, [center]);
  return null;
}

function ToastViewport({ notifications, dismiss }) {
  return (
    <div className="toast-viewport" role="status" aria-live="polite">
      {notifications.map((item) => (
        <div key={item.id} className={`toast toast-${item.type}`}>
          <div className="toast-icon">
            {item.type === "success" ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
          </div>
          <p>{item.message}</p>
          <button type="button" onClick={() => dismiss(item.id)} aria-label="Tutup notifikasi">
            <X size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}

export default function App() {
  const [notifications, setNotifications] = useState([]);
  const notify = (message, type = "error") => {
    const id = Date.now() + Math.random();
    setNotifications((items) => [...items, { id, message, type }]);
    setTimeout(() => setNotifications((items) => items.filter((item) => item.id !== id)), 4500);
  };
  const dismissNotification = (id) => {
    setNotifications((items) => items.filter((item) => item.id !== id));
  };

  // State edit laporan (benar: deklarasi di atas return/if)
  const [editReportModal, setEditReportModal] = useState({ open: false, report: null });
  const [editJudul, setEditJudul] = useState("");
  const [editIsi, setEditIsi] = useState("");
  const [editDeptId, setEditDeptId] = useState("");
  const [editLat, setEditLat] = useState("");
  const [editLong, setEditLong] = useState("");

  const openEditModal = (report) => {
    setEditReportModal({ open: true, report });
    setEditJudul(report.judul || "");
    setEditIsi(report.isi_laporan || "");
    setEditDeptId(report.dept_id ? String(report.dept_id) : "");
    setEditLat(report.lat || "");
    setEditLong(report.long || "");
  };

  const handleEditReport = async (e) => {
    e.preventDefault();
    if (!token || !editReportModal.report) return;
    try {
      const body = {
        judul: editJudul,
        isi_laporan: editIsi,
        dept_id: editDeptId ? parseInt(editDeptId, 10) : null,
        lat: editLat ? parseFloat(editLat) : null,
        long: editLong ? parseFloat(editLong) : null,
      };
      const res = await apiFetch(`/api/v1/reports/${editReportModal.report.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal update laporan");
      }
      setEditReportModal({ open: false, report: null });
      fetchReports();
      notify("Laporan berhasil diedit.", "success");
    } catch (e) {
      notify(e.message);
    }
  };

  const [mainView, setMainView] = useState("options"); // 'options' | 'pengaduan' | 'pertanyaan' | 'admin'
  const [token, setToken] = useState(
    localStorage.getItem("govsmart_token") || "",
  );
  const [userRole, setUserRole] = useState(
    localStorage.getItem("govsmart_role") || "",
  );
  const [userEmail, setUserEmail] = useState(
    localStorage.getItem("govsmart_email") || "",
  );

  // Auth Modal State
  const [authMode, setAuthMode] = useState("login"); // 'login' | 'register'
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [regNik, setRegNik] = useState("");
  const [authError, setAuthError] = useState("");

  // Warga Form State
  const [judul, setJudul] = useState("");
  const [isiLaporan, setIsiLaporan] = useState("");
  const [reportDeptId, setReportDeptId] = useState("");
  const [lat, setLat] = useState("");
  const [long, setLong] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadingFoto, setUploadingFoto] = useState(false);
  const [fotoFile, setFotoFile] = useState(null);
  const [fotoUploadMsg, setFotoUploadMsg] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [gpsLoading, setGpsLoading] = useState(false);

  // Reports Data State
  const [reports, setReports] = useState([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [departments, setDepartments] = useState([]);

  // Admin Audit & Update Modal State
  const [selectedReport, setSelectedReport] = useState(null);
  const [newStatus, setNewStatus] = useState("");
  const [catatanPetugas, setCatatanPetugas] = useState("");
  const [auditLogs, setAuditLogs] = useState([]);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [feedbackFile, setFeedbackFile] = useState(null);
  const [feedbackUploading, setFeedbackUploading] = useState(false);
  const [feedbackUploadMsg, setFeedbackUploadMsg] = useState("");

  const QUICK_PROMPTS = [
    "Berapa lama proses registrasi KKPR?",
    "Bagaimana syarat izin NIB UMKM?",
    "Apa saja syarat permohonan e-KTP baru?",
    "Bagaimana cara membuat laporan fasilitas rusak?",
  ];

  // Super Admin Register State
  const [adminNip, setAdminNip] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminDeptId, setAdminDeptId] = useState("");
  const [adminSuccess, setAdminSuccess] = useState("");
  const [adminDinasList, setAdminDinasList] = useState([]);
  const [editingAdmin, setEditingAdmin] = useState(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState("all"); // 'all' | 'diterima' | 'diproses' | 'selesai' | 'ditolak'
  const [dateFilter, setDateFilter] = useState("all"); // 'all' | 'day' | 'week' | 'month' | 'year'
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const [editForm, setEditForm] = useState({ nip: "", email: "", password: "", dept_id: "" });

  // AI Chatbot Widget State
  const [showChatbot, setShowChatbot] = useState(false);
  const [chatPrompt, setChatPrompt] = useState("");
  const [chatMessages, setChatMessages] = useState([
    {
      role: "ai",
      text: "Halo! Saya Asisten AI GovSmart. Ada yang bisa saya bantu terkait perizinan UMKM/NIB atau panduan layanan publik?",
    },
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  // Helper: compute date range from dateFilter / customStartDate / customEndDate
  const getPeriodRange = () => {
    const now = new Date();
    let start = null;
    let end = null;

    switch (dateFilter) {
      case "day":
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        end = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1);
        break;
      case "week":
        const dayOfWeek = now.getDay();
        start = new Date(now.getFullYear(), now.getMonth(), now.getDate() - dayOfWeek);
        end = new Date(start);
        end.setDate(end.getDate() + 7);
        break;
      case "month":
        start = new Date(now.getFullYear(), now.getMonth(), 1);
        end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
        end.setDate(end.getDate() + 1);
        break;
      case "year":
        start = new Date(now.getFullYear(), 0, 1);
        end = new Date(now.getFullYear() + 1, 0, 1);
        break;
      case "custom":
        if (customStartDate) start = new Date(customStartDate);
        if (customEndDate) {
          end = new Date(customEndDate);
          end.setDate(end.getDate() + 1);
        }
        break;
      default:
        break;
    }
    return { start, end };
  };

  // Fetch Reports & Departments
  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      const params = new URLSearchParams();
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (userRole === "warga") params.set("limit", "5");

      // Date filter: hitung start/end date berdasarkan periode yang dipilih
      const { start, end } = getPeriodRange();

      if (start) params.set("start_date", start.toISOString().split("T")[0]);
      if (end) params.set("end_date", end.toISOString().split("T")[0]);

       const res = await apiFetch(`/api/v1/reports/?${params}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setReports(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingReports(false);
    }
  };

  const fetchDepartments = async () => {
    try {
      const res = await apiFetch("/api/v1/departments/");
      if (res.ok) {
        const data = await res.json();
        setDepartments(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchNotifications = async () => {
    if (userRole !== "admin") return;
    try {
      const res = await apiFetch("/api/v1/reports/notifications/me", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const newCount = data.length;
        // Trigger browser notification + sound hanya saat ada laporan BARU (naik)
        if (typeof window !== "undefined" && newCount > unreadCount && document.visibilityState !== "visible") {
          try {
            const perm = await Notification.requestPermission();
            if (perm === "granted") {
              navigator.serviceWorker && navigator.serviceWorker.ready
                ? (await navigator.serviceWorker).active?.postMessage({ type: "newReport", count: newCount })
                : new Notification("GovSmart — Laporan Baru", {
                    body: `${newCount} laporan baru untuk dinas Anda`,
                    icon: "/favicon.svg",
                  });
              // Sound efek kecil (data URI, <1KB)
              const audio = new Audio("data:audio/wav;base64,UklGRlgAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YVgAAAFg////AYGA////AP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AAP//AAD//wAA//8AA==");
              audio.volume = 0.3;
              audio.play().catch(() => {});
            }
          } catch (e) {
            console.error("Notification error:", e);
          }
        }
        setUnreadCount(newCount);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Auto-refresh notifikasi setiap 15 detik (polling)
  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, [token, userRole]);

  // Refetch laporan ketika filter status berubah (kecuali saat token masih kosong — handled di bawah)
  const [reportsFetchedOnce, setReportsFetchedOnce] = useState(false);
  useEffect(() => {
    if (token) {
      fetchReports();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter, dateFilter, customStartDate, customEndDate]);

  useEffect(() => {
    fetchReports();
    fetchDepartments();
    fetchAdminDinas();
    if (!token) return;
    (async () => {
      try {
        const res = await apiFetch("/api/v1/chat/history?limit=20", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) return;
        const data = await res.json();
        const rows = (data.results || []).slice().reverse();
        if (!rows.length) return;
        setChatMessages([
          {
            role: "ai",
            text: "Halo! Saya Asisten AI GovSmart. Ada yang bisa saya bantu terkait perizinan UMKM/NIB atau panduan layanan publik?",
          },
          ...rows.flatMap((r) => [
            { role: "user", text: r.prompt },
            { role: "ai", text: r.response },
          ]),
        ]);
      } catch (_) { /* riwayat opsional */ }
    })();
  }, [token]);

  // Auth Handlers
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError("");
    try {
      const formData = new URLSearchParams();
      formData.append("username", loginEmail);
      formData.append("password", loginPassword);

      const res = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        let errorMsg = "Login gagal";
        if (typeof err.detail === "string") {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map((d) => d.msg).join(", ");
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      localStorage.setItem("govsmart_token", data.access_token);
      setToken(data.access_token);

      // Determine user role via /me
      const profileRes = await apiFetch("/api/v1/admin/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      if (profileRes.ok) {
        const profile = await profileRes.json();
        localStorage.setItem("govsmart_role", profile.role);
        localStorage.setItem("govsmart_email", profile.email);
        setUserRole(profile.role);
        setUserEmail(profile.email);

        setMainView("options");
      } else {
        setMainView("options");
      }
    } catch (e) {
      setAuthError(e.message);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError("");
    try {
      const res = await apiFetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: loginEmail,
          nik_or_nip: regNik,
          password: loginPassword,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        let errorMsg = "Registrasi gagal";
        if (typeof err.detail === "string") {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail
            .map((d) => {
              let msg = d.msg;
              if (msg.includes("String should have at least")) {
                const num = msg.match(/\d+/)?.[0] || "beberapa";
                msg = `Minimal ${num} karakter.`;
              } else if (msg.includes("String should have at most")) {
                const num = msg.match(/\d+/)?.[0] || "tertentu";
                msg = `Maksimal ${num} karakter.`;
              } else if (msg.includes("value is not a valid email")) {
                msg = `Format email tidak valid.`;
              }

              const field = d.loc?.[1];
              if (field === "nik_or_nip") return `NIK: ${msg}`;
              if (field === "password") return `Kata Sandi: ${msg}`;
              if (field === "email") return `Email: ${msg}`;
              return msg;
            })
            .join(" | ");
        }
        throw new Error(errorMsg);
      }

      // Auto login after register
      setAuthMode("login");
      notify("Registrasi berhasil. Silakan login.", "success");
    } catch (e) {
      setAuthError(e.message);
      notify(e.message);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken("");
    setUserRole("");
    setUserEmail("");
    setMainView("options");
  };

  // Submit Report Handler
  const handleSubmitReport = async (e) => {
    e.preventDefault();
    if (!token) {
      return;
    }
    setSubmitting(true);
    setSubmitSuccess(null);

    try {
      const body = {
        judul,
        isi_laporan: isiLaporan,
        dept_id: reportDeptId ? parseInt(reportDeptId, 10) : null,
        lat: lat ? parseFloat(lat) : null,
        long: long ? parseFloat(long) : null,
      };

      const res = await apiFetch("/api/v1/reports/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal mengirim laporan");
      }

      const data = await res.json();
      setSubmitSuccess(data);
      setJudul("");
      setIsiLaporan("");
      setReportDeptId("");
      setLat("");
      setLong("");

      // Jika ada foto yang dipilih, upload otomatis setelah laporan dibuat
      if (fotoFile) {
        setUploadingFoto(true);
        setFotoUploadMsg("⏳ Mengupload foto bukti...");
        try {
          const formData = new FormData();
          formData.append("foto", fotoFile);
          const fotoRes = await apiFetch(`/api/v1/reports/${data.id}/upload-foto`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
          if (fotoRes.ok) {
            setFotoUploadMsg("✅ Foto bukti berhasil diunggah!");
          } else {
            const fotoErr = await fotoRes.json();
            setFotoUploadMsg(`❌ ${fotoErr.detail || "Gagal mengupload foto"}`);
          }
        } catch {
          setFotoUploadMsg("❌ Gagal mengupload foto, koneksi terganggu.");
        } finally {
          setUploadingFoto(false);
          setFotoFile(null);
        }
      }

      fetchReports();
    } catch (e) {
      notify(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Upload Foto Handler
  const handleUploadFoto = async (reportId) => {
    if (!fotoFile) {
      setFotoUploadMsg("Pilih file foto terlebih dahulu.");
      return;
    }
    setUploadingFoto(true);
    setFotoUploadMsg("");
    try {
      const formData = new FormData();
      formData.append("foto", fotoFile);
      const res = await apiFetch(`/api/v1/reports/${reportId}/upload-foto`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal mengupload foto");
      }
      setFotoUploadMsg("✅ Foto bukti berhasil diunggah!");
      setFotoFile(null);
    } catch (e) {
      setFotoUploadMsg(`❌ ${e.message}`);
    } finally {
      setUploadingFoto(false);
    }
  };

  // GPS Auto-Fill Handler
  const handleUseGPS = () => {
    if (!navigator.geolocation) {
      notify("Browser Anda tidak mendukung Geolocation.");
      return;
    }
    setGpsLoading(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude.toFixed(6));
        setLong(pos.coords.longitude.toFixed(6));
        setGpsLoading(false);
      },
      () => {
        notify("Gagal mendapatkan lokasi. Pastikan izin lokasi diaktifkan.");
        setGpsLoading(false);
      }
    );
  };

  const handleCancelReport = async (reportId) => {
    if (!window.confirm("Batalkan pengaduan ini?")) return;
    try {
      const res = await apiFetch(`/api/v1/reports/${reportId}/cancel`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json();
        const detail = Array.isArray(err.detail)
          ? err.detail.map((item) => item.msg).join(", ")
          : err.detail;
        throw new Error(detail || "Gagal membatalkan pengaduan");
      }
      await fetchReports();
      notify("Pengaduan berhasil dibatalkan.", "success");
    } catch (e) {
      notify(e.message);
    }
  };

  // Status Update Handler
  const handleUpdateStatus = async (reportId) => {
    try {
      const res = await apiFetch(`/api/v1/reports/${reportId}/status`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          status: newStatus,
          catatan_petugas: catatanPetugas,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal memperbarui status");
      }

      fetchReports();
      setSelectedReport(null);
      setCatatanPetugas("");
      notify("Status laporan berhasil diperbarui.", "success");
    } catch (e) {
      notify(e.message);
    }
  };

  // Feedback Upload Handler (Admin Dinas)
  const handleUploadFeedback = async (e) => {
    e.preventDefault();
    if (!feedbackFile || !token || !selectedReport) return;
    setFeedbackUploading(true);
    setFeedbackUploadMsg("");
    try {
      const formData = new FormData();
      formData.append("foto", feedbackFile);
      const res = await apiFetch(`/api/v1/reports/${selectedReport.id}/upload-feedback`, {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal upload feedback");
      }
      const data = await res.json();
      setSelectedReport(data);
      setFeedbackFile(null);
      setFeedbackUploadMsg("✅ Dokumen feedback berhasil diunggah!");
      notify("Dokumen feedback berhasil diunggah.", "success");
    } catch (e) {
      setFeedbackUploadMsg(`❌ ${e.message}`);
      notify(e.message);
    } finally {
      setFeedbackUploading(false);
    }
  };

  // Export CSV Handler — gunakan backend export endpoint (filter sudah termasuk)
  const handleExportCSV = async () => {
    if (!reports || reports.length === 0) {
      notify("Tidak ada data laporan untuk diekspor.");
      return;
    }
    try {
      const params = new URLSearchParams();
      if (userRole === "warga") params.set("limit", "5");
      // Date filter via backend export
      const { start, end } = getPeriodRange();
      if (start) params.set("start_date", start.toISOString().split("T")[0]);
      if (end) params.set("end_date", end.toISOString().split("T")[0]);
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (userRole === "warga" && departments.length > 0) {
        const myDept = departments.find((d) => d.id === userDeptId);
        if (myDept) params.set("dept_id", myDept.id);
      }

      const res = await apiFetch(`/api/v1/reports/export/csv?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal mengekspor CSV");
      }
      const blob = new Blob([await res.text()], { type: "text/csv;charset=utf-8;" });
      const link = document.createElement("a");
      link.href = window.URL.createObjectURL(blob);
      link.download = `govsmart_laporan_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      notify("Berkas CSV laporan berhasil diunduh.", "success");
    } catch (e) {
      notify(e.message);
    }
  };

  // Export PDF Handler — fetch dengan token lalu buka sebagai blob di tab baru (print-to-PDF)
  const handleExportPDF = async () => {
    if (!reports || reports.length === 0) {
      notify("Tidak ada data laporan untuk diekspor.");
      return;
    }
    try {
      const params = new URLSearchParams();
      const { start, end } = getPeriodRange();
      if (start) params.set("start_date", start.toISOString().split("T")[0]);
      if (end) params.set("end_date", end.toISOString().split("T")[0]);
      if (statusFilter !== "all") params.set("status", statusFilter);

      const res = await apiFetch(`/api/v1/reports/export/html?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Gagal mengekspor PDF");
      }
      const html = await res.text();
      const blob = new Blob([html], { type: "text/html;charset=utf-8" });
      const url = window.URL.createObjectURL(blob);
      const win = window.open(url, "_blank");
      // Auto-revoke URL setelah tab terbuka
      if (win) setTimeout(() => window.URL.revokeObjectURL(url), 10000);
      notify("Halaman laporan terbuka. Gunakan Ctrl+P / Cmd+P untuk cetak sebagai PDF.", "success");
    } catch (e) {
      notify(e.message);
    }
  };

  // Clear Chat Handler
  const handleClearChat = async () => {
    setChatMessages([
      {
        role: "ai",
        text: "Halo! Percakapan telah dibersihkan. Ada yang bisa saya bantu seputar perizinan UMKM, layanan dinas, atau informasi Kabupaten Lamongan?",
      },
    ]);
    // Juga hapus riwayat dari backend supaya tidak muncul lagi setelah refresh
    const currentToken = token || localStorage.getItem("govsmart_token");
    if (currentToken) {
      try {
        await apiFetch("/api/v1/chat/history", {
          method: "DELETE",
          headers: { Authorization: "Bearer " + currentToken },
        });
      } catch (_) { /* backend clear opsional */ }
    }
    notify("Riwayat obrolan di layar dan di database telah dibersihkan.", "success");
  };

  // Fetch Audit Logs
  const handleViewAuditLogs = async (report) => {
    setSelectedReport(report);
    setShowAuditModal(true);
    try {
      const res = await apiFetch(`/api/v1/admin/audit-logs/${report.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Super Admin Create Admin Dinas
  const handleCreateAdminDinas = async (e) => {
    e.preventDefault();
    setAdminSuccess("");
    try {
      const res = await apiFetch("/api/v1/admin/admin-dinas", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          nip: adminNip,
          email: adminEmail,
          password: adminPassword,
          dept_id: adminDeptId ? parseInt(adminDeptId, 10) : undefined,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        let errorMsg = "Gagal membuat akun admin";
        if (typeof err.detail === "string") {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map((d) => d.msg).join(", ");
        } else if (err.detail) {
          errorMsg = JSON.stringify(err.detail);
        }
        throw new Error(errorMsg);
      }

      setAdminSuccess(`Akun Admin Dinas (${adminEmail}) berhasil dibuat!`);
      notify(`Akun Admin Dinas (${adminEmail}) berhasil dibuat.`, "success");
      setAdminNip("");
      setAdminEmail("");
      setAdminPassword("");
      setAdminDeptId("");
    } catch (e) {
      notify(e.message);
    }
  };

  // Fetch Admin Dinas list
  const fetchAdminDinas = async () => {
    try {
      const res = await apiFetch("/api/v1/admin/admin-dinas", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setAdminDinasList(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Edit Admin Dinas open
  const handleEditAdminDinas = (admin) => {
    setEditingAdmin(admin);
    setEditForm({
      nip: admin.nik_or_nip || "",
      email: admin.email || "",
      password: "",
      dept_id: admin.dept_id ? String(admin.dept_id) : "",
    });
  };

  // Save Admin Dinas edit
  const handleUpdateAdminDinas = async (e) => {
    e.preventDefault();
    try {
      const res = await apiFetch(`/api/v1/admin/admin-dinas/${editingAdmin.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          nip: editForm.nip,
          email: editForm.email,
          password: editForm.password || undefined,
          dept_id: editForm.dept_id ? parseInt(editForm.dept_id, 10) : undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        let errorMsg = "Gagal memperbarui akun";
        if (typeof err.detail === "string") errorMsg = err.detail;
        else if (Array.isArray(err.detail)) errorMsg = err.detail.map((d) => d.msg).join(", ");
        else if (err.detail) errorMsg = JSON.stringify(err.detail);
        throw new Error(errorMsg);
      }
      notify("Akun Admin Dinas berhasil diperbarui.", "success");
      setEditingAdmin(null);
      fetchAdminDinas();
    } catch (e) {
      notify(e.message);
    }
  };

  // Delete Admin Dinas
  const handleDeleteAdminDinas = async (admin) => {
    if (!window.confirm(`Hapus akun Admin Dinas ${admin.email}? Akun yang dinonaktifkan tidak dapat login.`)) return;
    try {
      const res = await apiFetch(`/api/v1/admin/admin-dinas/${admin.id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal menghapus akun");
      }
      notify("Akun Admin Dinas berhasil dinonaktifkan.", "success");
      fetchAdminDinas();
    } catch (e) {
      notify(e.message);
    }
  };

  // AI Chatbot Handler
  const chatErrorText = async (res) => {
    try {
      const err = await res.json();
      const d = err.detail;
      if (d && typeof d === "object" && d.pesan) return d.pesan;
      if (typeof d === "string") return d;
    } catch (_) { /* body bukan JSON */ }
    return "Maaf, terjadi kesalahan saat menghubungi server AI.";
  };

  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatPrompt.trim()) return;

    const userMsg = chatPrompt;
    setChatMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setChatPrompt("");
    setChatLoading(true);

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await apiFetch("/api/v1/chat/", {
        method: "POST",
        headers,
        body: JSON.stringify({ pertanyaan: userMsg }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages((prev) => [
          ...prev,
          { role: "ai", text: data.jawaban || "Tidak ada jawaban." },
        ]);
      } else {
        const text = await chatErrorText(res);
        setChatMessages((prev) => [...prev, { role: "ai", text }]);
      }
    } catch (e) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: "Koneksi terganggu. Silakan coba beberapa saat lagi.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  // Filtered reports by search query
  const filteredReports = reports.filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const judul = (r.judul || "").toLowerCase();
    const isi = (r.isi_laporan || "").toLowerCase();
    const dinas = (departments.find((d) => d.id === r.dept_id)?.nama_dinas || "").toLowerCase();
    const idStr = String(r.id);
    return judul.includes(q) || isi.includes(q) || dinas.includes(q) || idStr.includes(q);
  });

  // KPI Metrics Calculation
  const kpiTotal = reports.length;
  const kpiDarurat = reports.filter((r) => r.urgensi === "darurat").length;
  const kpiDiproses = reports.filter((r) => r.status === "diproses").length;
  const kpiSelesai = reports.filter((r) => r.status === "selesai").length;
  const kpiPersenSelesai = kpiTotal > 0 ? Math.round((kpiSelesai / kpiTotal) * 100) : 0;

  if (!token) {
    return (
      <div className="auth-page-overlay">
        <ToastViewport notifications={notifications} dismiss={dismissNotification} />
        <div className="auth-ambient auth-ambient-one" />
        <div className="auth-ambient auth-ambient-two" />

        <main className="auth-portal">
          <section className="auth-visual" aria-label="Tentang GovSmart">
            <div className="auth-brand-mark">
              <Sparkles size={30} />
            </div>
            <span className="auth-eyebrow">PEMERINTAH KABUPATEN LAMONGAN</span>
            <h1>GovSmart AI</h1>
            <p>
              Sistem pemerintah digital untuk laporan, layanan publik, dan akses
              informasi yang lebih cepat.
            </p>
            <div className="auth-visual-stats">
              <div>
                <strong>AI</strong>
                <span>Smart Routing</span>
              </div>
              <div>
                <strong>24/7</strong>
                <span>Layanan Digital</span>
              </div>
            </div>
          </section>

          <section className="auth-glass-card">
            <div className="auth-card-header">
              <div className="auth-brand-mini">
                <Sparkles size={20} />
                <span>GovSmart</span>
              </div>
              <span className="auth-secure">PORTAL LOGIN</span>
            </div>

            <div className="auth-heading">
              <span className="auth-kicker">SELAMAT DATANG</span>
              <h2>
                {authMode === "login" ? "Masuk ke portal" : "Buat akun baru"}
              </h2>
              <p>
                {authMode === "login"
                  ? "Akses layanan dan sistem pemerintah dengan aman."
                  : "Daftar untuk menggunakan layanan publik dan pengaduan."}
              </p>
            </div>

            {authError && <p className="auth-error">{authError}</p>}

            <div
              className={`auth-form-track ${authMode === "register" ? "is-register" : ""}`}
            >
              <form className="auth-form-panel" onSubmit={handleLogin}>
                <label className="auth-field">
                  <span>Alamat email</span>
                  <input
                    type="email"
                    className="auth-input"
                    placeholder="nama@email.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    autoComplete="email"
                    required
                  />
                </label>

                <label className="auth-field">
                  <span>Kata sandi</span>
                  <input
                    type="password"
                    className="auth-input"
                    placeholder="Masukkan kata sandi"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    autoComplete="current-password"
                    required
                  />
                </label>

                <button type="submit" className="auth-btn">
                  Masuk <span aria-hidden="true">→</span>
                </button>
              </form>

              <form className="auth-form-panel" onSubmit={handleRegister}>
                <label className="auth-field">
                  <span>NIK KTP (16 digit)</span>
                  <input
                    type="text"
                    className="auth-input"
                    placeholder="Contoh: 1234567890123456"
                    value={regNik}
                    onChange={(e) => setRegNik(e.target.value)}
                    autoComplete="off"
                    required
                  />
                </label>

                <label className="auth-field">
                  <span>Alamat email</span>
                  <input
                    type="email"
                    className="auth-input"
                    placeholder="nama@email.com"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    autoComplete="email"
                    required
                  />
                </label>

                <label className="auth-field">
                  <span>Kata sandi</span>
                  <input
                    type="password"
                    className="auth-input"
                    placeholder="Gunakan password kuat"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    autoComplete="new-password"
                    required
                  />
                </label>

                <button type="submit" className="auth-btn">
                  Daftar sekarang <span aria-hidden="true">→</span>
                </button>
              </form>
            </div>

            <div className="auth-switch">
              <span>
                {authMode === "login"
                  ? "Belum punya akun?"
                  : "Sudah punya akun?"}
              </span>
              <button
                type="button"
                className="auth-switch-link"
                onClick={() =>
                  setAuthMode(authMode === "login" ? "register" : "login")
                }
              >
                {authMode === "login" ? "Daftar baru" : "Masuk"}
              </button>
            </div>
          </section>
        </main>
      </div>
    );
  }

  if (mainView === "options") {
    return (
      <div
        className="portal-shell"
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <ToastViewport notifications={notifications} dismiss={dismissNotification} />
        <header className="navbar-solid portal-navbar">
          <div className="brand-logo">
            <Sparkles className="w-6 h-6 text-accent-primary" />
            <span>GovSmart AI</span>
          </div>
          <div>
            <span
              style={{
                fontSize: "1rem",
                fontWeight: 600,
                color: "var(--text-main)",
              }}
            >
              {userRole === "admin" && (
                <button
                  onClick={() => { setUnreadCount(0); setMainView("admin"); }}
                  style={{
                    background: "none",
                    border: "none",
                    color: "inherit",
                    cursor: "pointer",
                    marginRight: "0.5rem",
                    position: "relative",
                  }}
                  title="Dasbor Admin"
                >
                  <Bell size={18} />
                  {unreadCount > 0 && (
                    <span
                      style={{
                        position: "absolute",
                        top: "-4px",
                        right: "-4px",
                        background: "var(--accent-rose)",
                        color: "white",
                        fontSize: "0.65rem",
                        fontWeight: 700,
                        padding: "2px 5px",
                        borderRadius: "999px",
                        minWidth: "18px",
                        textAlign: "center",
                      }}
                    >
                      {unreadCount}
                    </span>
                  )}
                </button>
              )}
              {userEmail} ({userRole}) &nbsp;&bull;&nbsp;
              <button
                onClick={handleLogout}
                style={{
                  background: "none",
                  border: "none",
                  color: "var(--accent-rose)",
                  fontWeight: 700,
                  cursor: "pointer",
                  fontSize: "1rem",
                }}
              >
                Keluar
              </button>
            </span>
          </div>
        </header>

        <div
          className="portal-content"
          style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            padding: "2rem",
            animation: "fade-in-up 0.5s ease-out",
          }}
        >
          <h1
            style={{
              fontSize: "2.5rem",
              fontWeight: 800,
              marginBottom: "3rem",
              textAlign: "center",
              color: "var(--text-main)",
            }}
          >
            Pilih Layanan Anda
          </h1>
          <div
            style={{
              display: "flex",
              gap: "2rem",
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            {userRole === "admin" || userRole === "super_admin" ? (
              <div
                onClick={() => setMainView("admin")}
                className="glass-panel option-card"
              >
                <ShieldCheck size={80} className="text-accent-primary" />
                <h2 style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  Dasbor Admin
                </h2>
                <p style={{ textAlign: "center", color: "var(--text-muted)" }}>
                  Manajemen pengaduan masuk dan pembaruan status laporan.
                </p>
              </div>
            ) : (
              <>
                <div
                  onClick={() => setMainView("pengaduan")}
                  className="glass-panel option-card"
                >
                  <AlertTriangle size={80} className="text-accent-primary" />
                  <h2 style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                    Pengaduan
                  </h2>
                  <p
                    style={{ textAlign: "center", color: "var(--text-muted)" }}
                  >
                    Laporkan masalah infrastruktur atau layanan publik di
                    sekitar Anda.
                  </p>
                </div>

                <div
                  onClick={() => setMainView("pertanyaan")}
                  className="glass-panel option-card"
                >
                  <MessageSquare size={80} className="text-accent-primary" />
                  <h2 style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                    Pertanyaan
                  </h2>
                  <p
                    style={{ textAlign: "center", color: "var(--text-muted)" }}
                  >
                    Tanya AI Chatbot mengenai panduan layanan atau perizinan.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className="portal-shell"
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <ToastViewport notifications={notifications} dismiss={dismissNotification} />
      <header className="navbar-solid portal-navbar">
        <div
          className="brand-logo"
          onClick={() => setMainView("options")}
          style={{ cursor: "pointer" }}
        >
          <Sparkles className="w-6 h-6 text-accent-primary" />
          <span>GovSmart AI</span>
        </div>
        <div>
          <span
            style={{
              fontSize: "1rem",
              fontWeight: 600,
              color: "var(--text-main)",
            }}
          >
            {userEmail} ({userRole}) &nbsp;&bull;&nbsp;
            <button
              onClick={handleLogout}
              style={{
                background: "none",
                border: "none",
                color: "var(--accent-rose)",
                fontWeight: 700,
                cursor: "pointer",
                fontSize: "1rem",
              }}
            >
              Keluar
            </button>
          </span>
        </div>
      </header>

      <div
        className="portal-content"
        style={{
          padding: "2rem",
          maxWidth: "1200px",
          margin: "0 auto",
          width: "100%",
          animation: "fade-in-up 0.5s ease-out",
        }}
      >
        <button
          className="nav-btn"
          onClick={() => setMainView("options")}
          style={{ marginBottom: "2rem" }}
        >
          &larr; Kembali ke Pilihan
        </button>

        {mainView === "pengaduan" && (
          <div
            className="portal-report-layout"
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "3rem",
            }}
          >
            <div id="form-pengaduan" className="glass-panel">
              <h2
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  marginBottom: "1.5rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <FileText className="text-accent-primary" /> Buat Pengaduan Baru
              </h2>

              {submitSuccess && (
                <div
                  style={{
                    background: "#ecfdf5",
                    border: "1px solid #10b981",
                    padding: "1rem",
                    borderRadius: "12px",
                    marginBottom: "1.5rem",
                  }}
                >
                  <div
                    style={{
                      fontWeight: 700,
                      color: "#059669",
                      marginBottom: "0.25rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <CheckCircle size={18} /> Laporan Diterima & Teranalisis AI!
                  </div>
                  <p style={{ fontSize: "0.9rem", color: "var(--text-main)", marginBottom: "0.5rem" }}>
                    Urgency AI:{" "}
                    <span className={`badge badge-${submitSuccess.urgensi}`}>
                      {submitSuccess.urgensi}
                    </span>
                    {" "}| Dinas:{" "}
                    <strong>
                      {departments.find((d) => d.id === submitSuccess.dept_id)?.nama_dinas || "AI Auto-Routing"}
                    </strong>
                  </p>
                  {fotoUploadMsg && (
                    <p style={{ fontSize: "0.85rem", marginTop: "0.5rem", color: fotoUploadMsg.startsWith("✅") ? "#059669" : "#dc2626", fontWeight: 600 }}>
                      {fotoUploadMsg}
                    </p>
                  )}
                </div>
              )}

              <form onSubmit={handleSubmitReport}>
                <div className="form-group">
                  <label className="form-label">Judul Pengaduan</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Contoh: Jalan berlubang dan ambruk di Babat"
                    value={judul}
                    onChange={(e) => setJudul(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Dinas Tujuan (Opsional)</label>
                  <select
                    className="form-input"
                    value={reportDeptId}
                    onChange={(e) => setReportDeptId(e.target.value)}
                  >
                    <option value="">Otomatis oleh AI</option>
                    {departments.map((department) => (
                      <option key={department.id} value={department.id}>
                        {department.nama_dinas}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Isi Detail Laporan</label>
                  <textarea
                    className="form-textarea"
                    rows={5}
                    placeholder="Jelaskan lokasi rinci, kondisi, dan bahaya yang ditimbulkan..."
                    value={isiLaporan}
                    onChange={(e) => setIsiLaporan(e.target.value)}
                    required
                  />
                </div>
                {/* Koordinat Lokasi + Tombol GPS */}
                <div className="form-group">
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                    <label className="form-label" style={{ margin: 0 }}>Koordinat Lokasi Kejadian (Opsional)</label>
                    <button
                      type="button"
                      onClick={handleUseGPS}
                      disabled={gpsLoading}
                      style={{
                        display: "flex", alignItems: "center", gap: "0.35rem",
                        background: "var(--accent-primary)", color: "white",
                        border: "none", borderRadius: "8px", padding: "0.4rem 0.85rem",
                        fontSize: "0.8rem", fontWeight: 700, cursor: gpsLoading ? "not-allowed" : "pointer",
                        opacity: gpsLoading ? 0.7 : 1, transition: "all 0.2s",
                      }}
                    >
                      <Navigation size={13} />
                      {gpsLoading ? "Mendeteksi..." : "Gunakan Lokasi Saya"}
                    </button>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                    <input
                      type="number" step="any" className="form-input"
                      placeholder="Latitude, e.g. -7.1123"
                      value={lat} onChange={(e) => setLat(e.target.value)}
                    />
                    <input
                      type="number" step="any" className="form-input"
                      placeholder="Longitude, e.g. 112.1554"
                      value={long} onChange={(e) => setLong(e.target.value)}
                    />
                  </div>
                  {lat && long && (
                    <p style={{ fontSize: "0.8rem", color: "#059669", marginTop: "0.3rem", display: "flex", alignItems: "center", gap: "0.3rem" }}>
                      <MapPin size={12} /> Koordinat: {lat}, {long}
                    </p>
                  )}
                </div>

                {/* Upload Foto Bukti — Drag & Drop Zone */}
                <div className="form-group">
                  <label className="form-label">📎 Foto Bukti (Opsional, JPEG/PNG/WEBP, maks 5 MB)</label>
                  <div
                    onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                    onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }}
                    onDrop={(e) => {
                      e.preventDefault();
                      setIsDragging(false);
                      const file = e.dataTransfer.files[0];
                      if (file && ["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
                        setFotoFile(file);
                        setFotoUploadMsg("");
                      } else if (file) {
                        setFotoUploadMsg("❌ Format tidak didukung. Gunakan JPEG, PNG, atau WEBP.");
                      }
                    }}
                    onClick={() => document.getElementById("foto-input").click()}
                    style={{
                      border: `2px dashed ${isDragging ? "var(--accent-primary)" : fotoFile ? "#10b981" : "#cbd5e1"}`,
                      borderRadius: "12px",
                      padding: "1.5rem",
                      textAlign: "center",
                      cursor: "pointer",
                      background: isDragging
                        ? "rgba(79,70,229,0.06)"
                        : fotoFile
                        ? "rgba(16,185,129,0.05)"
                        : "#f8fafc",
                      transition: "all 0.2s ease",
                      userSelect: "none",
                    }}
                  >
                    <input
                      id="foto-input"
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      style={{ display: "none" }}
                      onChange={(e) => {
                        setFotoFile(e.target.files[0] || null);
                        setFotoUploadMsg("");
                      }}
                    />
                    {fotoFile ? (
                      <>
                        <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>🖼️</div>
                        <p style={{ fontWeight: 700, color: "#059669", marginBottom: "0.25rem", fontSize: "0.9rem" }}>
                          {fotoFile.name}
                        </p>
                        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          {(fotoFile.size / 1024 / 1024).toFixed(2)} MB — Klik untuk ganti
                        </p>
                      </>
                    ) : (
                      <>
                        <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>
                          {isDragging ? "📂" : "📤"}
                        </div>
                        <p style={{ fontWeight: 600, color: isDragging ? "var(--accent-primary)" : "var(--text-main)", marginBottom: "0.25rem", fontSize: "0.9rem" }}>
                          {isDragging ? "Lepaskan foto di sini" : "Drag & drop foto ke sini"}
                        </p>
                        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                          atau <span style={{ color: "var(--accent-primary)", fontWeight: 600 }}>klik untuk pilih file</span>
                        </p>
                      </>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  className="nav-btn nav-btn-primary"
                  style={{
                    width: "100%",
                    justifyContent: "center",
                    marginTop: "1rem",
                    padding: "0.85rem",
                  }}
                  disabled={submitting || uploadingFoto}
                >
                  <Send size={18} />{" "}
                  {submitting
                    ? "Menganalisis AI & Kirim..."
                    : uploadingFoto
                    ? "Mengupload Foto..."
                    : "Kirim Pengaduan"}
                </button>
              </form>
            </div>

            <div>
              <h2
                style={{
                  fontSize: "1.25rem",
                  fontWeight: 700,
                  marginBottom: "1.5rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <Clock className="text-accent-primary" /> Feed Pengaduan Publik
              </h2>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1.25rem",
                }}
              >
                {/* Search Bar Realtime */}
                <div style={{ position: "relative", marginBottom: "0.25rem" }}>
                  <Search size={16} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Cari laporan berdasarkan judul, isi, nama dinas, atau ID..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{ paddingLeft: "2.3rem", fontSize: "0.9rem" }}
                  />
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    marginBottom: "-0.5rem",
                  }}
                >
                  {["all", "diterima", "diproses", "selesai", "ditolak"].map((s) => (
                    <button
                      key={s}
                      onClick={() => setStatusFilter(s)}
                      className="nav-btn"
                      style={{
                        padding: "0.3rem 0.7rem",
                        fontSize: "0.78rem",
                        background: statusFilter === s ? "var(--accent-emerald)" : "transparent",
                        color: statusFilter === s ? "white" : "var(--text-muted)",
                        borderColor: statusFilter === s ? "var(--accent-emerald)" : "var(--border-color)",
                      }}
                    >
                      {s === "all"
                        ? "Semua"
                        : s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Date Period Filter + Export Buttons — untuk admin dan admin dinas */}
                {(userRole === "admin" || userRole === "admin_dinas") && (
                <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap", padding: "0.75rem 0", borderBottom: "1px solid var(--border-color)" }}>
                  <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", whiteSpace: "nowrap" }}>Filter Periode:</label>
                  <select
                    value={dateFilter}
                    onChange={(e) => { setDateFilter(e.target.value); if (e.target.value !== "custom") { setCustomStartDate(""); setCustomEndDate(""); } }}
                    style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border-color)", background: "var(--glass-bg)", color: "var(--text-primary)", fontSize: "0.85rem" }}
                  >
                    <option value="all">Semua Waktu</option>
                    <option value="day">Hari Ini</option>
                    <option value="week">Minggu Ini</option>
                    <option value="month">Bulan Ini</option>
                    <option value="year">Tahun Ini</option>
                    <option value="custom">Rentang Khusus</option>
                  </select>
                  {dateFilter === "custom" && (
                    <>
                      <input
                        type="date"
                        value={customStartDate}
                        onChange={(e) => setCustomStartDate(e.target.value)}
                        style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border-color)", background: "var(--glass-bg)", color: "var(--text-primary)", fontSize: "0.85rem" }}
                      />
                      <span style={{ color: "var(--text-muted)" }}>sd</span>
                      <input
                        type="date"
                        value={customEndDate}
                        onChange={(e) => setCustomEndDate(e.target.value)}
                        style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border-color)", background: "var(--glass-bg)", color: "var(--text-primary)", fontSize: "0.85rem" }}
                      />
                    </>
                  )}
                  <div style={{ flex: "auto" }} />
                  <button
                    onClick={handleExportCSV}
                    className="nav-btn"
                    style={{ padding: "0.3rem 0.8rem", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.3rem" }}
                  >
                    📎 Export CSV
                  </button>
                  <button
                    onClick={handleExportPDF}
                    className="nav-btn"
                    style={{ padding: "0.3rem 0.8rem", fontSize: "0.8rem", display: "flex", alignItems: "center", gap: "0.3rem" }}
                  >
                    📄 Export PDF
                  </button>
                </div>
                )}

                {filteredReports.length === 0 ? (
                  <div className="glass-panel" style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)", fontSize: "0.95rem" }}>
                    {searchQuery
                      ? `Tidak ditemukan laporan dengan kata kunci "${searchQuery}".`
                      : "Belum ada pengaduan pada kategori ini."}
                  </div>
                ) : (
                  filteredReports.map((report) => (
                    <div
                      key={report.id}
                      className="glass-panel"
                      style={{ padding: "1.5rem" }}
                    >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        marginBottom: "1rem",
                      }}
                    >
                      <span className={`badge badge-${report.urgensi}`}>
                        {report.urgensi === "darurat" && (
                          <AlertTriangle size={12} />
                        )}
                        {report.urgensi}
                      </span>
                      <span
                        style={{
                          fontSize: "0.85rem",
                          color: "var(--text-dim)",
                          fontWeight: 600,
                        }}
                      >
                        Status:{" "}
                        <strong style={{ color: "var(--accent-primary)" }}>
                          {report.status}
                        </strong>
                      </span>
                    </div>
                    <h3
                      style={{
                        fontSize: "1.15rem",
                        fontWeight: 700,
                        marginBottom: "0.5rem",
                        color: "var(--text-main)",
                      }}
                    >
                      {report.judul}
                    </h3>
                    <p
                      style={{
                        fontSize: "1rem",
                        color: "var(--text-muted)",
                        marginBottom: "1rem",
                        lineHeight: 1.6,
                      }}
                    >
                      {report.isi_laporan}
                    </p>
                    {report.foto_bukti && (
                      <div style={{ marginBottom: "1rem" }}>
                        <img
                          src={apiUrl(`/uploads/${report.foto_bukti}`)}
                          alt="Foto Bukti Kerusakan"
                          style={{
                            maxWidth: "100%",
                            maxHeight: "220px",
                            borderRadius: "10px",
                            objectFit: "cover",
                            border: "1px solid var(--border-color)",
                            cursor: "pointer",
                            boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
                          }}
                          onClick={() => window.open(apiUrl(`/uploads/${report.foto_bukti}`), "_blank")}
                          title="Klik untuk melihat foto ukuran penuh"
                        />
                      </div>
                    )}
                    {report.catatan_petugas && (
                      <div
                        style={{
                          marginBottom: "0.85rem",
                          padding: "0.75rem 1rem",
                          background: "rgba(16, 185, 129, 0.08)",
                          borderLeft: "4px solid #10b981",
                          borderRadius: "6px",
                          fontSize: "0.88rem",
                          color: "var(--text-main)",
                        }}
                      >
                        <strong style={{ color: "#059669", display: "block", marginBottom: "0.25rem", fontSize: "0.82rem" }}>
                          📌 Tindak Lanjut Dinas:
                        </strong>
                        {report.catatan_petugas}
                      </div>
                    )}
                    {/* Tombol lihat dokumen feedback dari admin dinas — hanya untuk warga */}
                    {userRole === "warga" && report.foto_feedback && (
                      <div
                        style={{
                          marginBottom: "0.85rem",
                          padding: "0.75rem 1rem",
                          background: "rgba(59, 130, 246, 0.07)",
                          borderLeft: "4px solid #3b82f6",
                          borderRadius: "6px",
                          display: "flex",
                          alignItems: "center",
                          gap: "0.75rem",
                        }}
                      >
                        <span style={{ fontSize: "0.85rem", color: "var(--text-main)", fontWeight: 600, flex: 1 }}>
                          📎 Dokumen Feedback Dinas tersedia
                        </span>
                        <a
                          href={apiUrl(`/uploads/${report.foto_feedback}`)}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.35rem",
                            padding: "0.35rem 0.85rem",
                            background: "#3b82f6",
                            color: "white",
                            borderRadius: "7px",
                            fontSize: "0.82rem",
                            fontWeight: 700,
                            textDecoration: "none",
                            whiteSpace: "nowrap",
                            boxShadow: "0 1px 4px rgba(59,130,246,0.25)",
                          }}
                        >
                          🔍 Lihat Dokumen
                        </a>
                      </div>
                    )}
                    {report.lat && report.long && (
                      <div style={{ marginBottom: "0.85rem" }}>
                        <a
                          href={`https://www.google.com/maps?q=${report.lat},${report.long}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: "0.35rem",
                            fontSize: "0.8rem",
                            color: "var(--accent-primary)",
                            textDecoration: "none",
                            background: "rgba(59, 130, 246, 0.08)",
                            padding: "0.3rem 0.65rem",
                            borderRadius: "6px",
                            fontWeight: 600,
                          }}
                        >
                          <MapPin size={13} /> Lokasi GPS ({report.lat}, {report.long})
                        </a>
                      </div>
                    )}
                    <div
                      style={{
                        fontSize: "0.85rem",
                        color: "var(--text-dim)",
                        display: "flex",
                        justifyContent: "space-between",
                        borderTop: "1px solid #e2e8f0",
                        paddingTop: "1rem",
                      }}
                    >
                      <span>
                        <Building2
                          size={14}
                          style={{ display: "inline", marginRight: "4px" }}
                        />{" "}
                        {departments.find((d) => d.id === report.dept_id)?.nama_dinas || "AI Auto-Routing"}
                      </span>
                      <span>
                        {formatDate(report.created_at, { dateStyle: "medium" })}
                      </span>
                    </div>
                    {userRole === "warga" && report.status === "diterima" && (
                      <>
                        <button
                          type="button"
                          className="nav-btn"
                          onClick={() => openEditModal(report)}
                          style={{ marginTop: "1rem", marginRight: "1rem" }}
                        >
                          Edit Pengaduan
                        </button>
                        <button
                          type="button"
                          className="nav-btn"
                          onClick={() => handleCancelReport(report.id)}
                          style={{ marginTop: "1rem", color: "#dc2626", borderColor: "#fecaca" }}
                        >
                          Batalkan Pengaduan
                        </button>
                      </>
                    )}
                  </div>
                ))
              )}
              </div>
            </div>
          </div>
        )}

        {mainView === "pertanyaan" && (
          <div
            className="glass-panel"
            style={{ padding: "2rem", maxWidth: "800px", margin: "0 auto" }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "1.5rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <Bot size={32} className="text-accent-primary" />
                <h2 style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                  Tanya AI GovSmart
                </h2>
              </div>
              <button
                type="button"
                className="nav-btn"
                onClick={handleClearChat}
                style={{ padding: "0.4rem 0.85rem", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
                title="Bersihkan riwayat percakapan di layar"
              >
                <RotateCcw size={14} /> Mulai Baru
              </button>
            </div>

            <div
              style={{
                height: "400px",
                overflowY: "auto",
                marginBottom: "2rem",
                padding: "1rem",
                background: "#f8fafc",
                borderRadius: "12px",
                border: "1px solid #e2e8f0",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`chat-msg ${msg.role === "user" ? "chat-msg-user" : "chat-msg-ai"}`}
                  style={{
                    maxWidth: "85%",
                    padding: "0.85rem 1.2rem",
                    borderRadius: "12px",
                    fontSize: "1rem",
                    lineHeight: 1.5,
                    alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
                    background:
                      msg.role === "user" ? "var(--accent-primary)" : "#ffffff",
                    color: msg.role === "user" ? "#ffffff" : "#000000",
                    border: msg.role === "user" ? "none" : "1px solid #e2e8f0",
                  }}
                >
                  {renderChatText(msg.text)}
                </div>
              ))}
              {chatLoading && (
                <div
                  className="chat-msg chat-msg-ai typing-indicator"
                  style={{
                    alignSelf: "flex-start",
                    background: "#ffffff",
                    border: "1px solid #e2e8f0",
                    borderRadius: "12px",
                  }}
                >
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              )}
            </div>

            {/* Rekomendasi Pertanyaan Cepat */}
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setChatPrompt(qp)}
                  className="nav-btn"
                  style={{
                    padding: "0.35rem 0.75rem",
                    fontSize: "0.78rem",
                    background: "rgba(59, 130, 246, 0.06)",
                    borderColor: "rgba(59, 130, 246, 0.25)",
                    color: "var(--accent-primary)",
                    borderRadius: "999px",
                    cursor: "pointer",
                  }}
                >
                  💡 {qp}
                </button>
              ))}
            </div>

            <form
              onSubmit={handleSendChat}
              style={{ display: "flex", gap: "1rem" }}
            >
              <input
                type="text"
                className="form-input"
                placeholder="Tanyakan panduan atau lapor..."
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                style={{ flex: 1 }}
              />
              <button
                type="submit"
                className="nav-btn nav-btn-primary"
                style={{ padding: "0.85rem 1.5rem" }}
              >
                <Send size={18} /> Kirim
              </button>
            </form>
          </div>
        )}

        {mainView === "admin" &&
          (userRole === "admin" || userRole === "super_admin") && (
            <div>
              <h1
                style={{
                  fontSize: "2rem",
                  fontWeight: 800,
                  marginBottom: "2rem",
                }}
              >
                Dasbor Manajemen & Penanganan Pengaduan
              </h1>

              {/* Kartu Ringkasan Statistik (KPI Metrics) */}
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "1.25rem",
                  marginBottom: "2rem",
                }}
              >
                <div className="glass-panel" style={{ padding: "1.25rem 1.5rem" }}>
                  <div style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontWeight: 600 }}>Total Pengaduan</div>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "var(--text-main)", marginTop: "0.25rem" }}>{kpiTotal}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>Semua kategori dinas</div>
                </div>

                <div className="glass-panel" style={{ padding: "1.25rem 1.5rem", borderLeft: "4px solid #ef4444" }}>
                  <div style={{ fontSize: "0.85rem", color: "#ef4444", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <AlertTriangle size={15} /> Urgensi Darurat
                  </div>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#ef4444", marginTop: "0.25rem" }}>{kpiDarurat}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>Prioritas penanganan utama</div>
                </div>

                <div className="glass-panel" style={{ padding: "1.25rem 1.5rem", borderLeft: "4px solid #f59e0b" }}>
                  <div style={{ fontSize: "0.85rem", color: "#d97706", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <Clock size={15} /> Sedang Diproses
                  </div>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#d97706", marginTop: "0.25rem" }}>{kpiDiproses}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>Dalam pengerjaan OPD</div>
                </div>

                <div className="glass-panel" style={{ padding: "1.25rem 1.5rem", borderLeft: "4px solid #10b981" }}>
                  <div style={{ fontSize: "0.85rem", color: "#059669", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <CheckCircle size={15} /> Selesai Ditangani
                  </div>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#059669", marginTop: "0.25rem" }}>
                    {kpiSelesai} <span style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-muted)" }}>({kpiPersenSelesai}%)</span>
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>Penyelesaian tuntas</div>
                </div>
              </div>
              {userRole === "super_admin" && (
                <div
                  className="glass-panel"
                  style={{ padding: "2rem", marginBottom: "2.5rem" }}
                >
                  <h2
                    style={{
                      fontSize: "1.2rem",
                      fontWeight: 700,
                      marginBottom: "1.5rem",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <UserPlus className="text-accent-primary" /> Registrasi Akun
                    Admin Dinas Baru
                  </h2>
                  {adminSuccess && (
                    <p
                      style={{
                        color: "#059669",
                        background: "#ecfdf5",
                        padding: "1rem",
                        borderRadius: "8px",
                        fontWeight: 600,
                        marginBottom: "1.5rem",
                      }}
                    >
                      {adminSuccess}
                    </p>
                  )}
                  <form
                    onSubmit={handleCreateAdminDinas}
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr 1fr auto",
                      gap: "1rem",
                      alignItems: "end",
                    }}
                  >
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label">NIP Aparatur</label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="198505052010011005"
                        value={adminNip}
                        onChange={(e) => setAdminNip(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label">Email Dinas</label>
                      <input
                        type="email"
                        className="form-input"
                        placeholder="admin.pu@lamongan.go.id"
                        value={adminEmail}
                        onChange={(e) => setAdminEmail(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label">Password</label>
                      <input
                        type="password"
                        className="form-input"
                        placeholder="••••••••"
                        value={adminPassword}
                        onChange={(e) => setAdminPassword(e.target.value)}
                        required
                      />
                    </div>
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label">Dinas</label>
                      <select
                        className="form-select"
                        value={adminDeptId}
                        onChange={(e) => setAdminDeptId(e.target.value)}
                        required
                      >
                        <option value="">Pilih Dinas</option>
                        {departments.map((d) => (
                          <option key={d.id} value={d.id}>{d.nama_dinas}</option>
                        ))}
                      </select>
                    </div>
                    <button
                      type="submit"
                      className="nav-btn nav-btn-primary"
                      style={{ padding: "0.85rem 1.5rem" }}
                    >
                      Buat Akun
                    </button>
                  </form>
                </div>
              )}{/* Daftar Admin Dinas (Super Admin only) */}
              {userRole === "super_admin" && (
                <div className="glass-panel" style={{ padding: "1.5rem", marginBottom: "2rem" }}>
                  <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <UserPlus className="text-accent-primary" /> Daftar Admin Dinas Terdaftar
                  </h2>
                  {adminDinasList.length === 0 ? (
                    <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>Belum ada Admin Dinas terdaftar.</p>
                  ) : (
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                      <thead>
                        <tr style={{ borderBottom: "2px solid var(--border-color)", textAlign: "left", color: "var(--text-muted)" }}>
                          <th style={{ padding: "0.75rem" }}>ID</th>
                          <th style={{ padding: "0.75rem" }}>NIP</th>
                          <th style={{ padding: "0.75rem" }}>Email</th>
                          <th style={{ padding: "0.75rem" }}>Dinas</th>
                          <th style={{ padding: "0.75rem" }}>Status</th>
                          <th style={{ padding: "0.75rem" }}>Aksi</th>
                        </tr>
                      </thead>
                      <tbody>
                        {adminDinasList.map((a) => (
                          <tr key={a.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                            <td style={{ padding: "0.75rem", fontWeight: 600 }}>#{a.id}</td>
                            <td style={{ padding: "0.75rem" }}>{a.nik_or_nip}</td>
                            <td style={{ padding: "0.75rem" }}>{a.email}</td>
                            <td style={{ padding: "0.75rem" }}>{a.nama_dinas || departments.find((d) => d.id === a.dept_id)?.nama_dinas || "-"}</td>
                            <td style={{ padding: "0.75rem" }}>{a.is_active ? "Aktif" : "Non-aktif"}</td>
                            <td style={{ padding: "0.75rem", display: "flex", gap: "0.3rem" }}>
                              <button
                                className="nav-btn"
                                style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem" }}
                                onClick={() => handleEditAdminDinas(a)}
                              >
                                Edit
                              </button>
                              <button
                                className="nav-btn"
                                style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#ef4444", color: "#ef4444" }}
                                onClick={() => handleDeleteAdminDinas(a)}
                              >
                                Hapus
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              )}{/* Peta Lamongan dengan Pin Laporan*/}
              <div className="glass-panel" style={{ padding: "1.5rem", marginBottom: "2rem" }}>
                <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <MapPin className="text-accent-primary" /> Peta Sebaran Laporan — Kabupaten Lamongan
                </h2>
                {/* Legenda Dinas */}
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
                  {departments.map((d, i) => (
                    <span key={d.id} style={{ display: "flex", alignItems: "center", gap: "0.3rem", fontSize: "0.75rem", background: "#f1f5f9", padding: "0.25rem 0.6rem", borderRadius: "999px", fontWeight: 600 }}>
                      <span style={{ width: 10, height: 10, borderRadius: "50%", background: DEPT_COLORS[i % DEPT_COLORS.length], display: "inline-block" }} />
                      {d.nama_dinas.replace("Dinas ", "")}
                    </span>
                  ))}
                </div>
                <div style={{ height: "420px", borderRadius: "12px", overflow: "hidden" }}>
                  <MapContainer
                    center={[-7.1189, 112.4109]}
                    zoom={11}
                    style={{ height: "100%", width: "100%" }}
                    scrollWheelZoom={true}
                  >
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>'
                    />
                    {reports
                      .filter((r) => r.lat && r.long)
                      .map((r) => {
                        const deptIdx = departments.findIndex((d) => d.id === r.dept_id);
                        const color = DEPT_COLORS[deptIdx >= 0 ? deptIdx % DEPT_COLORS.length : 0];
                        return (
                          <Marker
                            key={r.id}
                            position={[parseFloat(r.lat), parseFloat(r.long)]}
                            icon={createReportIcon(color)}
                          >
                            <Popup>
                              <div style={{ minWidth: "180px" }}>
                                <strong style={{ fontSize: "0.9rem" }}>{r.judul}</strong><br />
                                <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                                  {departments.find((d) => d.id === r.dept_id)?.nama_dinas || "AI Auto-Routing"}
                                </span><br />
                                <span style={{ fontSize: "0.75rem", fontWeight: 700, color: r.urgensi === "darurat" ? "#ef4444" : r.urgensi === "penting" ? "#f97316" : "#22c55e" }}>
                                  ● {r.urgensi.toUpperCase()}
                                </span>{" | "}
                                <span style={{ fontSize: "0.75rem" }}>{r.status}</span>
                              </div>
                            </Popup>
                          </Marker>
                        );
                      })}
                  </MapContainer>
                </div>
                {reports.filter((r) => r.lat && r.long).length === 0 && (
                  <p style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.75rem" }}>
                    Belum ada laporan dengan data koordinat lokasi.
                  </p>
                )}
              </div>

              <div className="glass-panel" style={{ padding: "1.5rem" }}>
                <div
                  style={{
                    marginBottom: "1.25rem",
                  }}
                >
                  <h2
                    style={{
                      fontSize: "1.2rem",
                      fontWeight: 700,
                      margin: 0,
                    }}
                  >
                    Daftar Pengaduan Masuk
                  </h2>
                </div>

                {/* Filter Tombol Status */}
                <div
                  style={{
                    display: "flex",
                    gap: "0.5rem",
                    flexWrap: "wrap",
                    marginBottom: "0.75rem",
                  }}
                >
                  {["all", "diterima", "diproses", "selesai", "ditolak"].map((s) => (
                    <button
                      key={s}
                      onClick={() => setStatusFilter(s)}
                      className="nav-btn"
                      style={{
                        padding: "0.3rem 0.8rem",
                        fontSize: "0.82rem",
                        fontWeight: 600,
                        background: statusFilter === s ? "var(--accent-emerald)" : "transparent",
                        color: statusFilter === s ? "white" : "var(--text-muted)",
                        borderColor: statusFilter === s ? "var(--accent-emerald)" : "var(--border-color)",
                        borderRadius: "8px",
                      }}
                    >
                      {s === "all" ? "Semua" : s.charAt(0).toUpperCase() + s.slice(1)}
                    </button>
                  ))}
                </div>

                {/* Filter Periode + Export PDF */}
                <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap", padding: "0.75rem 0", marginBottom: "1rem", borderBottom: "1px solid var(--border-color)" }}>
                  <label style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", whiteSpace: "nowrap" }}>Filter Periode:</label>
                  <select
                    value={dateFilter}
                    onChange={(e) => { setDateFilter(e.target.value); if (e.target.value !== "custom") { setCustomStartDate(""); setCustomEndDate(""); } }}
                    style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border-color)", background: "var(--glass-bg)", color: "var(--text-primary)", fontSize: "0.85rem" }}
                  >
                    <option value="all">Semua Waktu</option>
                    <option value="day">Hari Ini</option>
                    <option value="week">Minggu Ini</option>
                    <option value="month">Bulan Ini</option>
                    <option value="year">Tahun Ini</option>
                    <option value="custom">Rentang Khusus</option>
                  </select>
                  {dateFilter === "custom" && (
                    <>
                      <input
                        type="date"
                        value={customStartDate}
                        onChange={(e) => setCustomStartDate(e.target.value)}
                        style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border-color)", background: "var(--glass-bg)", color: "var(--text-primary)", fontSize: "0.85rem" }}
                      />
                      <span style={{ color: "var(--text-muted)" }}>s/d</span>
                      <input
                        type="date"
                        value={customEndDate}
                        onChange={(e) => setCustomEndDate(e.target.value)}
                        style={{ padding: "0.3rem 0.6rem", borderRadius: "6px", border: "1px solid var(--border-color)", background: "var(--glass-bg)", color: "var(--text-primary)", fontSize: "0.85rem" }}
                      />
                    </>
                  )}
                  <div style={{ flex: "auto" }} />
                  <button
                    onClick={handleExportCSV}
                    className="nav-btn"
                    style={{ padding: "0.3rem 0.8rem", fontSize: "0.8rem", display: "inline-flex", alignItems: "center", gap: "0.3rem" }}
                    title="Unduh data laporan ke format CSV / Excel"
                  >
                    <Download size={13} /> CSV
                  </button>
                  <button
                    onClick={handleExportPDF}
                    className="nav-btn"
                    style={{ padding: "0.3rem 0.8rem", fontSize: "0.8rem", display: "inline-flex", alignItems: "center", gap: "0.3rem" }}
                    title="Cetak laporan ke PDF via browser"
                  >
                    📄 PDF
                  </button>
                </div>

                {filteredReports.length === 0 ? (
                  <p style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem" }}>
                    {statusFilter !== "all" || dateFilter !== "all" ? `Tidak ada laporan yang cocok dengan filter yang dipilih.` : "Belum ada pengaduan masuk."}
                  </p>
                ) : (
                  <table
                    style={{
                      width: "100%",
                      borderCollapse: "collapse",
                      fontSize: "0.95rem",
                    }}
                  >
                    <thead>
                      <tr
                        style={{
                          borderBottom: "2px solid var(--border-color)",
                          textAlign: "left",
                          color: "var(--text-muted)",
                        }}
                      >
                        <th style={{ padding: "1rem" }}>ID</th>
                        <th style={{ padding: "1rem" }}>Urgensi AI</th>
                        <th style={{ padding: "1rem" }}>Judul Laporan</th>
                        <th style={{ padding: "1rem" }}>Status</th>
                        <th style={{ padding: "1rem" }}>Aksi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredReports.map((r) => (
                      <tr
                        key={r.id}
                        style={{ borderBottom: "1px solid #e2e8f0" }}
                      >
                        <td style={{ padding: "1rem", fontWeight: 600 }}>
                          #{r.id}
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <span className={`badge badge-${r.urgensi}`}>
                            {r.urgensi}
                          </span>
                        </td>
                        <td
                          style={{
                            padding: "1rem",
                            fontWeight: 700,
                            color: "var(--text-main)",
                          }}
                        >
                          {r.judul}
                        </td>
                        <td style={{ padding: "1rem" }}>
                          <span
                            style={{
                              color:
                                r.status === "selesai" ? "#059669" : "#b45309",
                              fontWeight: 700,
                            }}
                          >
                            {r.status}
                          </span>
                        </td>
                        <td
                          style={{
                            padding: "1rem",
                            display: "flex",
                            gap: "0.5rem",
                          }}
                        >
                          <button
                            className="nav-btn"
                            style={{
                              padding: "0.4rem 0.8rem",
                              fontSize: "0.85rem",
                            }}
                            onClick={() => {
                              setSelectedReport(r);
                              setNewStatus(r.status);
                              setCatatanPetugas(r.catatan_petugas || "");
                            }}
                          >
                            Ubah Status
                          </button>
                          <button
                            className="nav-btn"
                            style={{
                              padding: "0.4rem 0.8rem",
                              fontSize: "0.85rem",
                              borderColor: "var(--accent-primary)",
                              color: "var(--accent-primary)",
                            }}
                            onClick={() => handleViewAuditLogs(r)}
                          >
                            Audit Log
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modals for Admin Actions */}
      {selectedReport && !showAuditModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3
              style={{
                fontSize: "1.25rem",
                fontWeight: 800,
                marginBottom: "1rem",
              }}
            >
              Pembaruan Status Laporan #{selectedReport.id}
            </h3>
            <p
              style={{
                fontSize: "1.05rem",
                fontWeight: 700,
                color: "var(--text-main)",
                marginBottom: "0.5rem",
              }}
            >
              {selectedReport.judul}
            </p>
            <p
              style={{
                fontSize: "0.9rem",
                color: "var(--text-muted)",
                marginBottom: "1rem",
                lineHeight: 1.5,
                background: "rgba(0,0,0,0.02)",
                padding: "0.75rem",
                borderRadius: "8px",
                border: "1px solid var(--border-color)",
              }}
            >
              {selectedReport.isi_laporan}
            </p>
            {selectedReport.foto_bukti && (
              <div style={{ marginBottom: "1rem" }}>
                <p style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.25rem" }}>
                  Foto Bukti Lampiran:
                </p>
                <img
                  src={apiUrl(`/uploads/${selectedReport.foto_bukti}`)}
                  alt="Foto Bukti"
                  style={{
                    maxWidth: "100%",
                    maxHeight: "180px",
                    borderRadius: "8px",
                    objectFit: "cover",
                    border: "1px solid var(--border-color)",
                    cursor: "pointer",
                  }}
                  onClick={() => window.open(apiUrl(`/uploads/${selectedReport.foto_bukti}`), "_blank")}
                  title="Klik untuk membuka ukuran penuh"
                />
              </div>
            )}
            {selectedReport.lat && selectedReport.long && (
              <div style={{ marginBottom: "1rem" }}>
                <a
                  href={`https://www.google.com/maps?q=${selectedReport.lat},${selectedReport.long}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.35rem",
                    fontSize: "0.8rem",
                    color: "var(--accent-primary)",
                    textDecoration: "none",
                    background: "rgba(59, 130, 246, 0.08)",
                    padding: "0.3rem 0.65rem",
                    borderRadius: "6px",
                    fontWeight: 600,
                  }}
                >
                  <MapPin size={13} /> Lokasi GPS ({selectedReport.lat}, {selectedReport.long})
                </a>
              </div>
            )}
            <div className="form-group">
              <label className="form-label">Pilih Status Baru</label>
              <select
                className="form-select"
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
              >
                <option value="diterima">Diterima</option>
                <option value="diproses">Diproses</option>
                <option value="selesai">Selesai</option>
                <option value="ditolak">Ditolak</option>
              </select>
            </div>
            <div className="form-group" style={{ marginTop: "1rem" }}>
              <label className="form-label">Catatan / Tindak Lanjut Petugas (Opsional)</label>
              <textarea
                className="form-input"
                rows={3}
                placeholder="Tuliskan keterangan perbaikan, tindak lanjut tim lapangan, atau alasan penolakan..."
                value={catatanPetugas}
                onChange={(e) => setCatatanPetugas(e.target.value)}
                style={{ resize: "vertical" }}
              />
            </div>
            {/* Preview dokumen feedback jika sudah ada */}
            {selectedReport.foto_feedback && (
              <div style={{ marginBottom: "1rem" }}>
                <p style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)", marginBottom: "0.25rem" }}>
                  Dokumen Feedback yang Diupload:
                </p>
                {selectedReport.foto_feedback.toLowerCase().endsWith(".pdf") ? (
                  <a
                    href={apiUrl("/uploads/" + selectedReport.foto_feedback)}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ display: "inline-flex", alignItems: "center", gap: "0.35rem", fontSize: "0.9rem", color: "var(--accent-primary)" }}
                  >
                    📎 Buka Dokumen PDF
                  </a>
                ) : (
                  <img
                    src={apiUrl("/uploads/" + selectedReport.foto_feedback)}
                    alt="Foto Feedback"
                    style={{ maxWidth: "100%", maxHeight: "120px", borderRadius: "8px", objectFit: "cover", border: "1px solid var(--border-color)", cursor: "pointer" }}
                    onClick={() => window.open(apiUrl("/uploads/" + selectedReport.foto_feedback), "_blank")}
                  />
                )}
              </div>
            )}
            {/* Upload dokumen/foto feedback dari admin dinas */}
            <form onSubmit={handleUploadFeedback} style={{ marginTop: "1rem" }}>
              <label className="form-label">Upload Dokumen/Foto Feedback (Opsional)</label>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,application/pdf"
                onChange={(e) => setFeedbackFile(e.target.files[0] || null)}
                style={{ marginBottom: "0.5rem" }}
              />
              {feedbackUploadMsg && (
                <p style={{ fontSize: "0.8rem", marginTop: "0.3rem", color: feedbackUploadMsg.startsWith("✅") ? "#059669" : "#dc2626", fontWeight: 600 }}>
                  {feedbackUploadMsg}
                </p>
              )}
              <button
                type="submit"
                className="nav-btn"
                style={{ padding: "0.4rem 0.85rem", fontSize: "0.82rem" }}
                disabled={feedbackUploading || !feedbackFile}
              >
                {feedbackUploading ? "Mengupload..." : "Upload Feedback"}
              </button>
            </form>
            <div
              style={{
                display: "flex",
                gap: "1rem",
                justifyContent: "flex-end",
                marginTop: "2rem",
              }}
            >
              <button
                className="nav-btn"
                onClick={() => {
                  setSelectedReport(null);
                  setCatatanPetugas("");
                }}
              >
                Batal
              </button>
              <button
                className="nav-btn nav-btn-primary"
                onClick={() => handleUpdateStatus(selectedReport.id)}
              >
                Simpan Perubahan
              </button>
            </div>
          </div>
        </div>
      )}

      {showAuditModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "1.5rem",
              }}
            >
              <h3 style={{ fontSize: "1.25rem", fontWeight: 800 }}>
                Riwayat Status (Log #{selectedReport?.id})
              </h3>
              <button
                className="nav-btn"
                onClick={() => setShowAuditModal(false)}
              >
                <X size={20} />
              </button>
            </div>
            <div
              style={{
                maxHeight: "350px",
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              {auditLogs.map((log) => (
                <div
                  key={log.id}
                  style={{
                    background: "#f8fafc",
                    padding: "1rem",
                    borderRadius: "12px",
                    borderLeft: "4px solid var(--accent-primary)",
                  }}
                >
                  <div
                    style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}
                  >
                    Oleh User ID #{log.admin_id} &bull;{" "}
                    {formatDate(log.created_at)}
                  </div>
                  <div
                    style={{
                      fontSize: "1.05rem",
                      marginTop: "0.5rem",
                      color: "var(--text-main)",
                    }}
                  >
                    Status:{" "}
                    <span
                      style={{
                        textDecoration: "line-through",
                        color: "var(--text-dim)",
                      }}
                    >
                      {log.status_lama || "baru"}
                    </span>{" "}
                    &rarr;{" "}
                    <strong style={{ color: "var(--accent-primary)" }}>
                      {log.status_baru}
                    </strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}{/* Edit Admin Dinas Modal */}
      {editingAdmin && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontSize: "1.25rem", fontWeight: 800, marginBottom: "1rem" }}>
              Edit Admin Dinas — #{editingAdmin.id}
            </h3>
            <form onSubmit={handleUpdateAdminDinas}>
              <div className="form-group">
                <label className="form-label">NIP Aparatur</label>
                <input
                  type="text"
                  className="form-input"
                  value={editForm.nip}
                  onChange={(e) => setEditForm({ ...editForm, nip: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Email Dinas</label>
                <input
                  type="email"
                  className="form-input"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password Baru (kosongkan jika tidak diubah)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={editForm.password}
                  onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Dinas</label>
                <select
                  className="form-select"
                  value={editForm.dept_id}
                  onChange={(e) => setEditForm({ ...editForm, dept_id: e.target.value })}
                >
                  <option value="">Pilih Dinas</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>{d.nama_dinas}</option>
                  ))}
                </select>
              </div>
              <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end", marginTop: "2rem" }}>
                <button className="nav-btn" type="button" onClick={() => setEditingAdmin(null)}>
                  Batal
                </button>
                <button type="submit" className="nav-btn nav-btn-primary">
                  Simpan Perubahan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editReportModal.open && (
        <div className="modal-overlay" style={{ position: "fixed", zIndex: 50, left: 0, top: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.25)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div className="glass-panel" style={{ width: 420, maxWidth: "95vw", padding: 28, borderRadius: 16, boxShadow: "0 4px 32px rgba(0,0,0,0.15)" }}>
            <h2 style={{ fontSize: "1.2rem", fontWeight: 700, marginBottom: 16 }}>Edit Laporan</h2>
            <form onSubmit={handleEditReport}>
              <div className="form-group">
                <label className="form-label">Judul</label>
                <input type="text" className="form-input" value={editJudul} onChange={(e) => setEditJudul(e.target.value)} required />
              </div>
              <div className="form-group">
                <label className="form-label">Dinas Tujuan (Opsional)</label>
                <select className="form-input" value={editDeptId} onChange={(e) => setEditDeptId(e.target.value)}>
                  <option value="">Otomatis oleh AI</option>
                  {departments.map((department) => (
                    <option key={department.id} value={department.id}>{department.nama_dinas}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Isi Laporan</label>
                <textarea className="form-textarea" rows={4} value={editIsi} onChange={(e) => setEditIsi(e.target.value)} required />
              </div>
              <div className="form-group">
                <label className="form-label">Latitude (Opsional)</label>
                <input type="number" step="any" className="form-input" value={editLat} onChange={(e) => setEditLat(e.target.value)} />
              </div>
              <div className="form-group">
                <label className="form-label">Longitude (Opsional)</label>
                <input type="number" step="any" className="form-input" value={editLong} onChange={(e) => setEditLong(e.target.value)} />
              </div>
              <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end", gap: 12 }}>
                <button type="button" className="nav-btn" onClick={() => setEditReportModal({ open: false, report: null })}>Batal</button>
                <button type="submit" className="nav-btn nav-btn-primary">Simpan Perubahan</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
