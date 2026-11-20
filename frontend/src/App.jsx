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
  Users,
  Star,
  User,
  ChevronDown,
  Eye,
  EyeOff,
} from "lucide-react";

const RATING_LABELS = {
  1: "1/5 — Sangat Tidak Puas",
  2: "2/5 — Kurang Puas",
  3: "3/5 — Cukup Puas",
  4: "4/5 — Puas",
  5: "5/5 — Sangat Puas",
};
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const DEFAULT_PROD_API = "https://govsmart-main.onrender.com";
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.PROD ? DEFAULT_PROD_API : "")
).replace(/\/+$/, "");
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
  const elements = [];
  const listRegex = /^([-*•]|\d+[.)])\s+/;

  blocks.forEach((block, blockIndex) => {
    const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
    if (!lines.length) return;

    let i = 0;
    while (i < lines.length) {
      if (listRegex.test(lines[i])) {
        const ordered = /^\d+[.)]\s+/.test(lines[i]);
        const listItems = [];
        while (
          i < lines.length &&
          listRegex.test(lines[i]) &&
          (/^\d+[.)]\s+/.test(lines[i]) === ordered)
        ) {
          listItems.push(lines[i].replace(listRegex, ""));
          i++;
        }
        const Tag = ordered ? "ol" : "ul";
        elements.push(
          <Tag key={`${blockIndex}-list-${i}`} className="chat-list">
            {listItems.map((item, itemIdx) => (
              <li key={itemIdx}>{item}</li>
            ))}
          </Tag>
        );
      } else {
        const textLines = [];
        while (i < lines.length && !listRegex.test(lines[i])) {
          textLines.push(lines[i]);
          i++;
        }
        elements.push(<p key={`${blockIndex}-p-${i}`}>{textLines.join("\n")}</p>);
      }
    }
  });

  return elements;
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

function MapInvalidateSize({ trigger }) {
  const map = useMap();
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 90);
    return () => clearTimeout(timer);
  }, [trigger, map]);
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
  const [editFotoFile, setEditFotoFile] = useState(null);
  const [editUploadingFoto, setEditUploadingFoto] = useState(false);

  const openEditModal = (report) => {
    setEditReportModal({ open: true, report });
    setEditJudul(report.judul || "");
    setEditIsi(report.isi_laporan || "");
    setEditDeptId(report.dept_id ? String(report.dept_id) : "");
    setEditLat(report.lat || "");
    setEditLong(report.long || "");
    setEditFotoFile(null);
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

      if (editFotoFile) {
        setEditUploadingFoto(true);
        try {
          const formData = new FormData();
          formData.append("foto", editFotoFile);
          const fotoRes = await apiFetch(`/api/v1/reports/${editReportModal.report.id}/upload-foto`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,
          });
          if (!fotoRes.ok) {
            const fotoErr = await fotoRes.json().catch(() => ({}));
            throw new Error(fotoErr.detail || "Laporan diperbarui, tetapi gagal mengunggah foto bukti baru");
          }
        } finally {
          setEditUploadingFoto(false);
        }
      }

      setEditReportModal({ open: false, report: null });
      setEditFotoFile(null);
      fetchReports();
      notify("Laporan berhasil diperbarui.", "success");
    } catch (e) {
      notify(e.message);
    }
  };

  const [mainView, setMainView] = useState("options"); // 'options' | 'pengaduan' | 'pertanyaan' | 'admin' | 'admin_dinas'
  const [token, setToken] = useState(
    localStorage.getItem("govsmart_token") || "",
  );
  const [userRole, setUserRole] = useState(
    localStorage.getItem("govsmart_role") || "",
  );
  const [userEmail, setUserEmail] = useState(
    localStorage.getItem("govsmart_email") || "",
  );
  const [userProfile, setUserProfile] = useState(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileForm, setProfileForm] = useState({
    nama_lengkap: "",
    email: "",
    no_telepon: "",
    alamat: "",
    password: "",
  });
  const userMenuRef = useRef(null);

  useEffect(() => {
    if (!userMenuOpen) return;
    const handleClickOutside = (event) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === "Escape") setUserMenuOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [userMenuOpen]);

  // Auth Modal State
  const [authMode, setAuthMode] = useState("login"); // 'login' | 'register' | 'forgot'
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [regNik, setRegNik] = useState("");
  const [authError, setAuthError] = useState("");
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotNik, setForgotNik] = useState("");
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotNewPassword, setForgotNewPassword] = useState("");
  const [forgotSubmitting, setForgotSubmitting] = useState(false);
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);

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
    "Daftar pertanyaan yang bisa ditanyakan?",
    "Berapa lama proses registrasi KKPR?",
    "Bagaimana syarat izin NIB UMKM?",
    "Apa saja syarat permohonan e-KTP baru?",
    "Bagaimana cara membuat laporan fasilitas rusak?",
    "Bagaimana cara memberi rating kepuasan laporan?",
    "Bagaimana cara edit profil pengguna?",
  ];

  // Super Admin Register State
  const [adminNip, setAdminNip] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [adminDeptId, setAdminDeptId] = useState("");
  const [adminSuccess, setAdminSuccess] = useState("");
  const [adminDinasList, setAdminDinasList] = useState([]);
  const [adminDeptFilter, setAdminDeptFilter] = useState("all");
  const [adminSearchQuery, setAdminSearchQuery] = useState("");
  const [showInactiveAdmins, setShowInactiveAdmins] = useState(false);
  const [adminMobileTab, setAdminMobileTab] = useState("peta"); // 'peta' | 'daftar'
  const [mapDeptFilter, setMapDeptFilter] = useState("all");
  const [mapStatusMode, setMapStatusMode] = useState("active"); // 'active' | 'all'
  const [showMapLegend, setShowMapLegend] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState(null);
  const [wargaList, setWargaList] = useState([]);
  const [wargaSearchQuery, setWargaSearchQuery] = useState("");
  const [showInactiveWarga, setShowInactiveWarga] = useState(false);
  const [editingWarga, setEditingWarga] = useState(null);
  const [editWargaForm, setEditWargaForm] = useState({
    nama_lengkap: "",
    email: "",
    no_telepon: "",
    alamat: "",
    password: "",
  });
  const [unreadCount, setUnreadCount] = useState(0);
  const [statusFilter, setStatusFilter] = useState("all"); // 'all' | 'diterima' | 'diproses' | 'selesai' | 'ditolak'
  const [dateFilter, setDateFilter] = useState("all"); // 'all' | 'day' | 'week' | 'month' | 'year'
  const [customStartDate, setCustomStartDate] = useState("");
  const [customEndDate, setCustomEndDate] = useState("");
  const [editForm, setEditForm] = useState({ nip: "", email: "", password: "", dept_id: "" });

  // AI Chatbot Widget State
  const DEFAULT_CHAT_WELCOME = [
    {
      role: "ai",
      text: "Halo! Saya Asisten AI GovSmart. Ada yang bisa saya bantu terkait perizinan UMKM/NIB atau panduan layanan publik?",
    },
  ];
  const [showChatbot, setShowChatbot] = useState(false);
  const [chatPrompt, setChatPrompt] = useState("");
  const [chatMessages, setChatMessages] = useState(DEFAULT_CHAT_WELCOME);
  const [chatLoading, setChatLoading] = useState(false);
  const chatContainerRef = useRef(null);
  const chatEndRef = useRef(null);
  const chatInputRef = useRef(null);

  const scrollToLatestChat = (behavior = "smooth") => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior, block: "end" });
    } else if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior,
      });
    }
  };

  useEffect(() => {
    if (mainView === "pertanyaan") {
      const timer = setTimeout(() => {
        scrollToLatestChat("smooth");
      }, 50);
      return () => clearTimeout(timer);
    }
  }, [chatMessages, chatLoading, mainView]);

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
                    icon: "/favicon.png",
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
    let cancelled = false;
    // Selalu reset riwayat chat di layar setiap kali akun / token berganti agar riwayat per user terisolasi
    setChatMessages(DEFAULT_CHAT_WELCOME);
    setChatPrompt("");

    if (!token) {
      setReports([]);
      setUserProfile(null);
      setUserMenuOpen(false);
      setShowProfileModal(false);
      return;
    }

    fetchReports();
    fetchDepartments();

    (async () => {
      try {
        const profRes = await apiFetch("/api/v1/admin/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (profRes.ok && !cancelled) {
          const profData = await profRes.json();
          if (!cancelled) {
            setUserProfile(profData);
            if (profData.role) setUserRole(profData.role);
            if (profData.email) setUserEmail(profData.email);
            if (profData.role === "super_admin") {
              fetchAdminDinas(showInactiveAdmins);
              fetchWargaList(showInactiveWarga);
            }
          }
        }
      } catch (_) { /* profil opsional */ }
    })();

    (async () => {
      try {
        const res = await apiFetch("/api/v1/chat/history?limit=20", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok || cancelled) return;
        const data = await res.json();
        if (cancelled) return;
        const rows = (data.results || []).slice().reverse();
        if (!rows.length) {
          setChatMessages(DEFAULT_CHAT_WELCOME);
          return;
        }
        setChatMessages([
          ...DEFAULT_CHAT_WELCOME,
          ...rows.flatMap((r) => [
            { role: "user", text: r.prompt },
            { role: "ai", text: r.response },
          ]),
        ]);
      } catch (_) { /* riwayat opsional */ }
    })();

    return () => {
      cancelled = true;
    };
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

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setForgotSubmitting(true);
    try {
      const res = await apiFetch("/api/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nik_or_nip: forgotNik.trim(),
          email: forgotEmail.trim(),
          new_password: forgotNewPassword,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let errorMsg = "Gagal mereset kata sandi";
        if (typeof err.detail === "string") {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map((d) => d.msg).join(" | ");
        }
        throw new Error(errorMsg);
      }
      setShowForgotModal(false);
      setLoginEmail(forgotEmail.trim());
      setLoginPassword("");
      setForgotNik("");
      setForgotNewPassword("");
      notify("Kata sandi berhasil diperbarui! Silakan masuk dengan kata sandi baru.", "success");
    } catch (err) {
      notify(err.message);
    } finally {
      setForgotSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken("");
    setUserRole("");
    setUserEmail("");
    setUserProfile(null);
    setUserMenuOpen(false);
    setShowProfileModal(false);
    setMainView("options");
    setChatMessages(DEFAULT_CHAT_WELCOME);
    setChatPrompt("");
    setReports([]);
    setRatingDrafts({});
    setEditingRatingId(null);
    setSelectedReport(null);
    setShowAuditModal(false);
    setUnreadCount(0);
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
      // Date filter via backend export
      const { start, end } = getPeriodRange();
      if (start) params.set("start_date", start.toISOString().split("T")[0]);
      if (end) params.set("end_date", end.toISOString().split("T")[0]);
      if (statusFilter !== "all") params.set("status", statusFilter);

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
      fetchAdminDinas();
    } catch (e) {
      notify(e.message);
    }
  };

  // Fetch Admin Dinas list
  const fetchAdminDinas = async (includeInactive = showInactiveAdmins) => {
    try {
      const query = includeInactive ? "?include_inactive=true" : "";
      const res = await apiFetch(`/api/v1/admin/admin-dinas${query}`, {
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

  // Activate deactivated Admin Dinas
  const handleActivateAdminDinas = async (admin) => {
    try {
      const res = await apiFetch(`/api/v1/admin/admin-dinas/${admin.id}/activate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Gagal mengaktifkan kembali akun");
      }
      notify(`Akun Admin Dinas (${admin.email}) berhasil diaktifkan kembali.`, "success");
      fetchAdminDinas(showInactiveAdmins);
    } catch (e) {
      notify(e.message);
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
  const handleDeleteAdminDinas = async (admin, hard = false) => {
    const msg = hard
      ? `Hapus PERMANEN akun Admin Dinas ${admin.email} dari database?`
      : `Nonaktifkan akun Admin Dinas ${admin.email}? Akun yang dinonaktifkan tidak dapat login.`;
    if (!window.confirm(msg)) return;
    try {
      const url = hard
        ? `/api/v1/admin/admin-dinas/${admin.id}?hard=true`
        : `/api/v1/admin/admin-dinas/${admin.id}`;
      const res = await apiFetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Gagal menghapus akun");
      }
      notify(hard ? "Akun Admin Dinas dihapus permanen." : "Akun Admin Dinas berhasil dinonaktifkan.", "success");
      fetchAdminDinas(showInactiveAdmins);
    } catch (e) {
      notify(e.message);
    }
  };

  // Fetch Warga Users list (Super Admin)
  const fetchWargaList = async (includeInactive = showInactiveWarga) => {
    try {
      const query = includeInactive ? "?include_inactive=true" : "";
      const res = await apiFetch(`/api/v1/admin/warga${query}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setWargaList(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleEditWarga = (w) => {
    setEditingWarga(w);
    setEditWargaForm({
      nama_lengkap: w.nama_lengkap || "",
      email: w.email || "",
      no_telepon: w.no_telepon || "",
      alamat: w.alamat || "",
      password: "",
    });
  };

  const handleUpdateWarga = async (e) => {
    e.preventDefault();
    if (!editingWarga) return;
    try {
      const payload = {
        nama_lengkap: editWargaForm.nama_lengkap,
        email: editWargaForm.email,
        no_telepon: editWargaForm.no_telepon,
        alamat: editWargaForm.alamat,
      };
      if (editWargaForm.password.trim()) {
        payload.password = editWargaForm.password.trim();
      }
      const res = await apiFetch(`/api/v1/admin/warga/${editingWarga.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let errorMsg = "Gagal memperbarui akun warga";
        if (typeof err.detail === "string") errorMsg = err.detail;
        else if (Array.isArray(err.detail)) errorMsg = err.detail.map((d) => d.msg).join(" | ");
        throw new Error(errorMsg);
      }
      notify("Akun warga berhasil diperbarui.", "success");
      setEditingWarga(null);
      fetchWargaList(showInactiveWarga);
    } catch (err) {
      notify(err.message);
    }
  };

  const handleDeleteWarga = async (w, hard = false) => {
    const msg = hard
      ? `Hapus PERMANEN akun warga ${w.email} dari database?`
      : `Nonaktifkan akun warga ${w.email}? Akun yang dinonaktifkan tidak dapat login.`;
    if (!window.confirm(msg)) return;
    try {
      const url = hard ? `/api/v1/admin/warga/${w.id}?hard=true` : `/api/v1/admin/warga/${w.id}`;
      const res = await apiFetch(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Gagal menghapus akun warga");
      }
      notify(hard ? "Akun warga dihapus permanen." : "Akun warga berhasil dinonaktifkan.", "success");
      fetchWargaList(showInactiveWarga);
    } catch (err) {
      notify(err.message);
    }
  };

  const handleActivateWarga = async (w) => {
    try {
      const res = await apiFetch(`/api/v1/admin/warga/${w.id}/activate`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Gagal mengaktifkan kembali akun warga");
      }
      notify(`Akun warga (${w.email}) berhasil diaktifkan kembali.`, "success");
      fetchWargaList(showInactiveWarga);
    } catch (err) {
      notify(err.message);
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

  // State Penilaian Kepuasan Warga (per report ID)
  const [ratingDrafts, setRatingDrafts] = useState({});
  const [editingRatingId, setEditingRatingId] = useState(null);
  const [submittingRatingId, setSubmittingRatingId] = useState(null);

  const getRatingDraft = (report) => {
    if (ratingDrafts[report.id]) return ratingDrafts[report.id];
    return {
      rating: report.rating_kepuasan || 5,
      ulasan: report.ulasan_warga || "",
    };
  };

  const setRatingDraftField = (report, field, value) => {
    const current = getRatingDraft(report);
    setRatingDrafts((prev) => ({
      ...prev,
      [report.id]: { ...current, [field]: value },
    }));
  };

  const handleSubmitRating = async (report) => {
    const draft = getRatingDraft(report);
    if (!draft.rating || draft.rating < 1 || draft.rating > 5) {
      notify("Silakan pilih penilaian bintang 1 sampai 5.");
      return;
    }
    setSubmittingRatingId(report.id);
    try {
      const res = await apiFetch(`/api/v1/reports/${report.id}/rating`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          rating_kepuasan: Number(draft.rating),
          ulasan_warga: draft.ulasan ? draft.ulasan.trim() : null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Gagal menyimpan penilaian kepuasan");
      }
      setEditingRatingId(null);
      await fetchReports();
      notify("Terima kasih! Penilaian kepuasan Anda telah tersimpan.", "success");
    } catch (e) {
      notify(e.message);
    } finally {
      setSubmittingRatingId(null);
    }
  };

  const sendChatMessage = async (rawPrompt) => {
    const text = String(rawPrompt || "").trim();
    if (!text || chatLoading) return;

    // Susun riwayat percakapan (Multi-Turn Memory) dari pasangan pesan user & AI sebelumnya
    const riwayatPairs = [];
    for (let i = 1; i < chatMessages.length - 1; i++) {
      if (chatMessages[i].role === "user" && chatMessages[i + 1]?.role === "ai") {
        riwayatPairs.push({
          prompt: chatMessages[i].text,
          response: chatMessages[i + 1].text,
        });
      }
    }
    const recentRiwayat = riwayatPairs.slice(-10);

    setChatMessages((prev) => [...prev, { role: "user", text }]);
    setChatPrompt("");
    setChatLoading(true);
    chatInputRef.current?.focus();

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await apiFetch("/api/v1/chat/", {
        method: "POST",
        headers,
        body: JSON.stringify({ pertanyaan: text, riwayat: recentRiwayat }),
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages((prev) => [
          ...prev,
          {
            role: "ai",
            text: data.jawaban || "Tidak ada jawaban.",
            sumber: Array.isArray(data.sumber) ? data.sumber : [],
            intent: data.intent,
            konteks_sebelumnya: data.konteks_sebelumnya || null,
          },
        ]);
      } else {
        const errText = await chatErrorText(res);
        setChatMessages((prev) => [...prev, { role: "ai", text: errText }]);
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

  const handleSendChat = (e) => {
    e.preventDefault();
    sendChatMessage(chatPrompt);
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

  // Filtered Admin Dinas list by department name / search query
  const filteredAdminDinas = adminDinasList.filter((a) => {
    const deptName = (
      a.nama_dinas ||
      departments.find((d) => d.id === a.dept_id)?.nama_dinas ||
      ""
    ).toLowerCase();
    if (adminDeptFilter !== "all" && String(a.dept_id || "") !== adminDeptFilter) {
      return false;
    }
    if (adminSearchQuery.trim()) {
      const q = adminSearchQuery.trim().toLowerCase();
      const email = (a.email || "").toLowerCase();
      const nip = (a.nik_or_nip || "").toLowerCase();
      return deptName.includes(q) || email.includes(q) || nip.includes(q);
    }
    return true;
  });

  // Filtered Warga list by search query
  const filteredWargaList = wargaList.filter((w) => {
    if (!wargaSearchQuery.trim()) return true;
    const q = wargaSearchQuery.trim().toLowerCase();
    return (
      (w.nama_lengkap || "").toLowerCase().includes(q) ||
      (w.email || "").toLowerCase().includes(q) ||
      (w.nik_or_nip || "").toLowerCase().includes(q) ||
      (w.no_telepon || "").toLowerCase().includes(q) ||
      (w.alamat || "").toLowerCase().includes(q)
    );
  });

  // KPI Metrics Calculation
  const kpiTotal = reports.length;
  const kpiDarurat = reports.filter((r) => r.urgensi === "darurat").length;
  const kpiDiproses = reports.filter((r) => r.status === "diproses").length;
  const kpiSelesai = reports.filter((r) => r.status === "selesai").length;
  const kpiPersenSelesai = kpiTotal > 0 ? Math.round((kpiSelesai / kpiTotal) * 100) : 0;
  const ratedReports = reports.filter((r) => Number(r.rating_kepuasan) >= 1 && Number(r.rating_kepuasan) <= 5);
  const kpiAvgRating =
    ratedReports.length > 0
      ? (ratedReports.reduce((acc, r) => acc + Number(r.rating_kepuasan), 0) / ratedReports.length).toFixed(1)
      : null;

  // Map Filtering Calculation (Decluttered Map for Admin / Super Admin)
  const allCoordReports = reports.filter((r) => r.lat && r.long);
  const coordReportsByDept = allCoordReports.filter(
    (r) => mapDeptFilter === "all" || String(r.dept_id || "") === mapDeptFilter,
  );
  const activeCoordReportsByDept = coordReportsByDept.filter(
    (r) => r.status === "diterima" || r.status === "diproses",
  );
  const mapFilteredReports =
    mapStatusMode === "active" ? activeCoordReportsByDept : coordReportsByDept;

  const formatRoleLabel = (role) => {
    if (role === "super_admin") return "Super Admin";
    if (role === "admin" || role === "admin_dinas") return "Admin Dinas";
    return "Warga";
  };

  const displayName = userProfile?.nama_lengkap || userEmail;
  const userInitial = (displayName || "U").trim().charAt(0).toUpperCase();
  const profileDeptName =
    userProfile?.nama_dinas ||
    (userProfile?.dept_id
      ? departments.find((d) => Number(d.id) === Number(userProfile.dept_id))?.nama_dinas
      : null);

  const openProfileEdit = () => {
    setProfileForm({
      nama_lengkap: userProfile?.nama_lengkap || "",
      email: userProfile?.email || userEmail || "",
      no_telepon: userProfile?.no_telepon || "",
      alamat: userProfile?.alamat || "",
      password: "",
    });
    setIsEditingProfile(true);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!token) return;
    setSavingProfile(true);
    try {
      const payload = {
        nama_lengkap: profileForm.nama_lengkap.trim(),
        email: profileForm.email.trim(),
        no_telepon: profileForm.no_telepon.trim(),
        alamat: profileForm.alamat.trim(),
      };
      if (profileForm.password.trim()) {
        payload.password = profileForm.password.trim();
      }
      const res = await apiFetch("/api/v1/admin/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        let errorMsg = "Gagal menyimpan perubahan profil";
        if (typeof err.detail === "string") {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map((d) => d.msg).join(" | ");
        }
        throw new Error(errorMsg);
      }
      const data = await res.json();
      setUserProfile(data);
      if (data.email) {
        setUserEmail(data.email);
        localStorage.setItem("govsmart_email", data.email);
      }
      if (data.access_token) {
        localStorage.setItem("govsmart_token", data.access_token);
        setToken(data.access_token);
      }
      setIsEditingProfile(false);
      setProfileForm((prev) => ({ ...prev, password: "" }));
      notify("Profil pengguna berhasil diperbarui.", "success");
    } catch (err) {
      notify(err.message);
    } finally {
      setSavingProfile(false);
    }
  };

  const renderAccountDropdown = (showBell = false) => (
    <div className="user-nav-actions">
      {showBell && userRole === "admin" && (
        <button
          type="button"
          className="user-bell-btn"
          onClick={() => {
            setUnreadCount(0);
            setMainView("admin");
          }}
          title="Notifikasi Laporan Masuk"
        >
          <Bell size={19} />
          {unreadCount > 0 && <span className="user-bell-badge">{unreadCount}</span>}
        </button>
      )}
      <div className="user-menu-wrapper" ref={userMenuRef}>
        <button
          type="button"
          className={`user-menu-trigger ${userMenuOpen ? "is-open" : ""}`}
          onClick={() => setUserMenuOpen((open) => !open)}
          aria-expanded={userMenuOpen}
          aria-haspopup="menu"
        >
          <span className="user-avatar-circle">{userInitial}</span>
          <span className="user-menu-meta">
            <span className="user-menu-email">{displayName}</span>
            <span className="user-menu-role">{formatRoleLabel(userRole)}</span>
          </span>
          <ChevronDown size={16} className="user-menu-chevron" />
        </button>

        {userMenuOpen && (
          <div className="user-dropdown-menu" role="menu">
            <div className="user-dropdown-header">
              <div className="user-dropdown-email">{displayName}</div>
              {userProfile?.nama_lengkap && (
                <div style={{ fontSize: "0.78rem", color: "#486581", marginTop: "0.15rem", wordBreak: "break-all" }}>
                  {userEmail}
                </div>
              )}
              <span className="user-dropdown-role-badge">{formatRoleLabel(userRole)}</span>
            </div>
            <button
              type="button"
              role="menuitem"
              className="user-dropdown-item"
              onClick={() => {
                setUserMenuOpen(false);
                setIsEditingProfile(false);
                setShowProfileModal(true);
              }}
            >
              <User size={16} />
              <span>Lihat Profil Pengguna</span>
            </button>
            <div className="user-dropdown-divider" />
            <button
              type="button"
              role="menuitem"
              className="user-dropdown-item user-dropdown-logout"
              onClick={() => {
                setUserMenuOpen(false);
                handleLogout();
              }}
            >
              <LogOut size={16} />
              <span>Keluar (Logout)</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );

  const renderProfileModal = () =>
    showProfileModal && (
      <div
        className="modal-overlay"
        onClick={() => {
          setShowProfileModal(false);
          setIsEditingProfile(false);
        }}
      >
        <div
          className="modal-content"
          onClick={(e) => e.stopPropagation()}
          style={{ maxWidth: "500px", maxHeight: "90vh", overflowY: "auto", padding: "2rem" }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1.25rem",
            }}
          >
            <h3 style={{ fontSize: "1.25rem", fontWeight: 800, margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <User size={22} className="text-accent-primary" />
              {isEditingProfile ? "Edit Profil Pengguna" : "Profil Pengguna"}
            </h3>
            <button
              type="button"
              className="nav-btn"
              onClick={() => {
                setShowProfileModal(false);
                setIsEditingProfile(false);
              }}
              style={{ padding: "0.35rem" }}
              aria-label="Tutup profil"
            >
              <X size={20} />
            </button>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              padding: "1rem",
              background: "#edf4fa",
              borderRadius: "12px",
              border: "1px solid rgba(14, 86, 168, 0.18)",
              marginBottom: "1.25rem",
            }}
          >
            <div
              style={{
                width: "54px",
                height: "54px",
                borderRadius: "50%",
                background: "linear-gradient(135deg, #0e56a8, #072b5e)",
                color: "#f5d01a",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.4rem",
                fontWeight: 800,
                flexShrink: 0,
                border: "2px solid #f2cb05",
              }}
            >
              {userInitial}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontWeight: 800, fontSize: "1rem", color: "#0d223a", wordBreak: "break-word" }}>
                {userProfile?.nama_lengkap || userProfile?.email || userEmail}
              </div>
              {userProfile?.nama_lengkap && (
                <div style={{ fontSize: "0.84rem", color: "#486581", wordBreak: "break-all" }}>
                  {userProfile?.email || userEmail}
                </div>
              )}
              <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "0.35rem", flexWrap: "wrap" }}>
                <span
                  style={{
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    padding: "0.2rem 0.6rem",
                    borderRadius: "999px",
                    background: "#0e56a8",
                    color: "#ffffff",
                  }}
                >
                  {formatRoleLabel(userProfile?.role || userRole)}
                </span>
                <span
                  style={{
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    padding: "0.2rem 0.6rem",
                    borderRadius: "999px",
                    background: "rgba(21, 128, 61, 0.14)",
                    color: "#15803d",
                  }}
                >
                  {userProfile?.is_active === false ? "Non-aktif" : "Akun Aktif"}
                </span>
              </div>
            </div>
          </div>

          {!isEditingProfile ? (
            <>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", fontSize: "0.94rem" }}>
                <div className="profile-info-row">
                  <span>Nama Lengkap</span>
                  <strong>{userProfile?.nama_lengkap || "-"}</strong>
                </div>
                <div className="profile-info-row">
                  <span>{userRole === "warga" ? "NIK KTP" : "NIP Aparatur"}</span>
                  <strong>{userProfile?.nik_or_nip || "-"}</strong>
                </div>
                <div className="profile-info-row">
                  <span>Alamat Email</span>
                  <strong>{userProfile?.email || userEmail || "-"}</strong>
                </div>
                <div className="profile-info-row">
                  <span>No. Telepon / WA</span>
                  <strong>{userProfile?.no_telepon || "-"}</strong>
                </div>
                <div className="profile-info-row">
                  <span>Alamat Domisili</span>
                  <strong>{userProfile?.alamat || "-"}</strong>
                </div>
                <div className="profile-info-row">
                  <span>Instansi / Dinas</span>
                  <strong>
                    {profileDeptName ||
                      (userRole === "super_admin"
                        ? "Pemerintah Kabupaten Lamongan (Pusat)"
                        : "Masyarakat / UMKM Kabupaten Lamongan")}
                  </strong>
                </div>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.75rem", marginTop: "1.75rem", flexWrap: "wrap" }}>
                <button
                  type="button"
                  className="nav-btn"
                  onClick={() => {
                    setShowProfileModal(false);
                    handleLogout();
                  }}
                  style={{
                    background: "#fef2f2",
                    color: "#dc2626",
                    borderColor: "#fecaca",
                    padding: "0.55rem 1rem",
                    fontSize: "0.9rem",
                  }}
                >
                  <LogOut size={16} /> Keluar
                </button>
                <div style={{ display: "flex", gap: "0.65rem" }}>
                  <button
                    type="button"
                    className="nav-btn"
                    onClick={() => setShowProfileModal(false)}
                    style={{ borderColor: "var(--border-color)", padding: "0.55rem 1rem", fontSize: "0.9rem" }}
                  >
                    Tutup
                  </button>
                  <button
                    type="button"
                    className="nav-btn nav-btn-primary"
                    onClick={openProfileEdit}
                    style={{ padding: "0.55rem 1.15rem", fontSize: "0.9rem" }}
                  >
                    Edit Profil
                  </button>
                </div>
              </div>
            </>
          ) : (
            <form onSubmit={handleSaveProfile}>
              <div className="form-group" style={{ marginBottom: "1rem" }}>
                <label className="form-label" style={{ fontSize: "0.9rem" }}>
                  {userRole === "warga" ? "NIK KTP (Tidak dapat diubah)" : "NIP Aparatur (Tidak dapat diubah)"}
                </label>
                <input
                  type="text"
                  className="form-input"
                  value={userProfile?.nik_or_nip || "-"}
                  disabled
                  readOnly
                  style={{
                    background: "#f1f5f9",
                    color: "#64748b",
                    cursor: "not-allowed",
                    fontSize: "0.95rem",
                    padding: "0.7rem 0.95rem",
                  }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "1rem" }}>
                <label className="form-label" style={{ fontSize: "0.9rem" }}>Nama Lengkap</label>
                <input
                  type="text"
                  className="form-input"
                  maxLength={120}
                  placeholder="Masukkan nama lengkap Anda"
                  value={profileForm.nama_lengkap}
                  onChange={(e) => setProfileForm({ ...profileForm, nama_lengkap: e.target.value })}
                  style={{ fontSize: "0.95rem", padding: "0.7rem 0.95rem" }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "1rem" }}>
                <label className="form-label" style={{ fontSize: "0.9rem" }}>Alamat Email</label>
                <input
                  type="email"
                  className="form-input"
                  required
                  value={profileForm.email}
                  onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                  style={{ fontSize: "0.95rem", padding: "0.7rem 0.95rem" }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "1rem" }}>
                <label className="form-label" style={{ fontSize: "0.9rem" }}>No. Telepon / WhatsApp</label>
                <input
                  type="tel"
                  className="form-input"
                  maxLength={30}
                  placeholder="Contoh: 081234567890"
                  value={profileForm.no_telepon}
                  onChange={(e) => setProfileForm({ ...profileForm, no_telepon: e.target.value })}
                  style={{ fontSize: "0.95rem", padding: "0.7rem 0.95rem" }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "1rem" }}>
                <label className="form-label" style={{ fontSize: "0.9rem" }}>Alamat Domisili</label>
                <input
                  type="text"
                  className="form-input"
                  maxLength={255}
                  placeholder="Contoh: Jl. Lamongrejo No. 10, Kec. Lamongan"
                  value={profileForm.alamat}
                  onChange={(e) => setProfileForm({ ...profileForm, alamat: e.target.value })}
                  style={{ fontSize: "0.95rem", padding: "0.7rem 0.95rem" }}
                />
              </div>

              <div className="form-group" style={{ marginBottom: "1.25rem" }}>
                <label className="form-label" style={{ fontSize: "0.9rem" }}>
                  Kata Sandi Baru (Opsional)
                </label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="Kosongkan jika tidak ingin mengubah kata sandi"
                  value={profileForm.password}
                  onChange={(e) => setProfileForm({ ...profileForm, password: e.target.value })}
                  style={{ fontSize: "0.95rem", padding: "0.7rem 0.95rem" }}
                />
                <span style={{ fontSize: "0.78rem", color: "#486581" }}>
                  Jika diisi: min. 8 karakter dengan huruf besar, huruf kecil, angka, dan simbol (!@#$%).
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
                <button
                  type="button"
                  className="nav-btn"
                  onClick={() => setIsEditingProfile(false)}
                  disabled={savingProfile}
                  style={{ borderColor: "var(--border-color)", padding: "0.6rem 1.1rem", fontSize: "0.9rem" }}
                >
                  Batal
                </button>
                <button
                  type="submit"
                  className="nav-btn nav-btn-primary"
                  disabled={savingProfile}
                  style={{ padding: "0.6rem 1.25rem", fontSize: "0.9rem" }}
                >
                  {savingProfile ? "Menyimpan..." : "Simpan Perubahan"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    );

  if (!token) {
    return (
      <div className="auth-page-overlay">
        <ToastViewport notifications={notifications} dismiss={dismissNotification} />
        <div className="auth-ambient auth-ambient-one" />
        <div className="auth-ambient auth-ambient-two" />

        <main className="auth-portal">
          <section className="auth-visual" aria-label="Tentang GovSmart">
            <div className="auth-brand-mark">
              <img
                src="/logo-lamongan.png"
                alt="Logo Kabupaten Lamongan"
                className="brand-crest-img auth-crest-lg"
              />
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
                <img
                  src="/logo-lamongan.png"
                  alt="Logo Kabupaten Lamongan"
                  className="brand-crest-img auth-crest-sm"
                />
                <span>GovSmart Lamongan</span>
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
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span>Kata sandi</span>
                    <button
                      type="button"
                      onClick={() => {
                        setForgotEmail(loginEmail);
                        setShowForgotModal(true);
                      }}
                      style={{
                        background: "none",
                        border: "none",
                        padding: 0,
                        fontSize: "0.78rem",
                        fontWeight: 700,
                        color: "#0e56a8",
                        cursor: "pointer",
                        textDecoration: "underline",
                      }}
                    >
                      Lupa kata sandi?
                    </button>
                  </div>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showLoginPassword ? "text" : "password"}
                      className="auth-input"
                      placeholder="Masukkan kata sandi"
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      autoComplete="current-password"
                      style={{ paddingRight: "2.75rem" }}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowLoginPassword((v) => !v)}
                      aria-label={showLoginPassword ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
                      title={showLoginPassword ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
                      style={{
                        position: "absolute",
                        right: "0.75rem",
                        top: "50%",
                        transform: "translateY(-50%)",
                        background: "none",
                        border: "none",
                        padding: "0.25rem",
                        cursor: "pointer",
                        color: "#486581",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {showLoginPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
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
                  <div style={{ position: "relative" }}>
                    <input
                      type={showRegisterPassword ? "text" : "password"}
                      className="auth-input"
                      placeholder="Gunakan password kuat"
                      value={loginPassword}
                      onChange={(e) => setLoginPassword(e.target.value)}
                      autoComplete="new-password"
                      style={{ paddingRight: "2.75rem" }}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegisterPassword((v) => !v)}
                      aria-label={showRegisterPassword ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
                      title={showRegisterPassword ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
                      style={{
                        position: "absolute",
                        right: "0.75rem",
                        top: "50%",
                        transform: "translateY(-50%)",
                        background: "none",
                        border: "none",
                        padding: "0.25rem",
                        cursor: "pointer",
                        color: "#486581",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {showRegisterPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
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

        {showForgotModal && (
          <div className="modal-overlay" onClick={() => setShowForgotModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "440px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h3 style={{ fontSize: "1.2rem", fontWeight: 800, margin: 0 }}>Reset Kata Sandi</h3>
                <button type="button" className="nav-btn" onClick={() => setShowForgotModal(false)} style={{ padding: "0.35rem" }}>
                  <X size={18} />
                </button>
              </div>
              <p style={{ fontSize: "0.86rem", color: "#486581", marginBottom: "1rem", lineHeight: 1.5 }}>
                Masukkan <strong>NIK/NIP</strong> dan <strong>Alamat Email</strong> yang terdaftar pada akun Anda untuk membuat kata sandi baru.
              </p>
              <form onSubmit={handleResetPassword}>
                <div className="form-group" style={{ marginBottom: "0.9rem" }}>
                  <label className="form-label">NIK KTP / NIP (16–20 digit)</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Masukkan NIK atau NIP terdaftar"
                    value={forgotNik}
                    onChange={(e) => setForgotNik(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group" style={{ marginBottom: "0.9rem" }}>
                  <label className="form-label">Alamat Email Terdaftar</label>
                  <input
                    type="email"
                    className="form-input"
                    placeholder="nama@email.com"
                    value={forgotEmail}
                    onChange={(e) => setForgotEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group" style={{ marginBottom: "1.25rem" }}>
                  <label className="form-label">Kata Sandi Baru</label>
                  <div style={{ position: "relative" }}>
                    <input
                      type={showForgotPassword ? "text" : "password"}
                      className="form-input"
                      placeholder="Min. 8 karakter (Huruf besar, kecil, angka, simbol)"
                      value={forgotNewPassword}
                      onChange={(e) => setForgotNewPassword(e.target.value)}
                      style={{ paddingRight: "2.75rem" }}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowForgotPassword((v) => !v)}
                      aria-label={showForgotPassword ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
                      title={showForgotPassword ? "Sembunyikan kata sandi" : "Lihat kata sandi"}
                      style={{
                        position: "absolute",
                        right: "0.75rem",
                        top: "50%",
                        transform: "translateY(-50%)",
                        background: "none",
                        border: "none",
                        padding: "0.25rem",
                        cursor: "pointer",
                        color: "#486581",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      {showForgotPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem" }}>
                  <button type="button" className="nav-btn" onClick={() => setShowForgotModal(false)}>
                    Batal
                  </button>
                  <button type="submit" className="nav-btn nav-btn-primary" disabled={forgotSubmitting}>
                    {forgotSubmitting ? "Memproses..." : "Simpan Kata Sandi Baru"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
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
            <img
              src="/logo-lamongan.png"
              alt="Logo Kabupaten Lamongan"
              className="brand-crest-img nav-crest-img"
            />
            <span>GovSmart Lamongan</span>
          </div>
          {renderAccountDropdown(true)}
        </header>
        {renderProfileModal()}

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
            className="options-hero-title"
            style={{
              fontSize: "clamp(1.75rem, 4.5vw, 2.5rem)",
              fontWeight: 800,
              marginBottom: "clamp(1.5rem, 4vw, 3rem)",
              textAlign: "center",
              color: "var(--text-main)",
            }}
          >
            Pilih Layanan Anda
          </h1>
          <div
            className="options-grid"
            style={{
              display: "flex",
              gap: "2rem",
              flexWrap: "wrap",
              justifyContent: "center",
              width: "100%",
            }}
          >
            {userRole === "admin" || userRole === "super_admin" ? (
              <>
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

                <div
                  onClick={() => setMainView("pertanyaan")}
                  className="glass-panel option-card"
                >
                  <MessageSquare size={80} className="text-accent-primary" />
                  <h2 style={{ fontSize: "1.75rem", fontWeight: 800 }}>
                    Bantuan
                  </h2>
                  <p style={{ textAlign: "center", color: "var(--text-muted)" }}>
                    Tanya AI Chatbot mengenai panduan layanan atau perizinan.
                  </p>
                </div>
              </>
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
                    Bantuan
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
          <img
            src="/logo-lamongan.png"
            alt="Logo Kabupaten Lamongan"
            className="brand-crest-img nav-crest-img"
          />
          <span>GovSmart Lamongan</span>
        </div>
        {renderAccountDropdown(true)}
      </header>
      {renderProfileModal()}

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
          onClick={() =>
            setMainView(
              mainView === "admin_dinas" || mainView === "user_warga"
                ? "admin"
                : "options"
            )
          }
          style={{ marginBottom: "2rem" }}
        >
          &larr;{" "}
          {mainView === "admin_dinas" || mainView === "user_warga"
            ? "Kembali ke Dasbor Admin"
            : "Kembali ke Pilihan"}
        </button>

        {mainView === "pengaduan" && (
          <div className="portal-report-layout">
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
                  <div className="coord-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.5rem" }}>
                    <label className="form-label" style={{ margin: 0 }}>Koordinat Lokasi Kejadian (Opsional)</label>
                    <button
                      type="button"
                      onClick={handleUseGPS}
                      disabled={gpsLoading}
                      style={{
                        display: "flex", alignItems: "center", gap: "0.35rem",
                        background: "var(--accent-primary)", color: "white",
                        border: "none", borderRadius: "8px", padding: "0.45rem 0.85rem",
                        fontSize: "0.8rem", fontWeight: 700, cursor: gpsLoading ? "not-allowed" : "pointer",
                        opacity: gpsLoading ? 0.7 : 1, transition: "all 0.2s",
                      }}
                    >
                      <Navigation size={13} />
                      {gpsLoading ? "Mendeteksi..." : "Gunakan Lokasi Saya"}
                    </button>
                  </div>
                  <div className="coord-grid">
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
                  {["all", "diterima", "diproses", "selesai", "ditolak", "dibatalkan"].map((s) => (
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

                    {/* Penilaian Kepuasan Warga untuk laporan berstatus selesai */}
                    {report.status === "selesai" && (
                      <div
                        style={{
                          marginBottom: "1rem",
                          padding: "1rem 1.15rem",
                          background: "#fffbeb",
                          border: "1px solid #fde68a",
                          borderLeft: "4px solid #f59e0b",
                          borderRadius: "8px",
                        }}
                      >
                        {userRole === "warga" && (!report.rating_kepuasan || editingRatingId === report.id) ? (
                          <div>
                            <div
                              style={{
                                fontWeight: 700,
                                fontSize: "0.95rem",
                                color: "#92400e",
                                marginBottom: "0.35rem",
                                display: "flex",
                                alignItems: "center",
                                gap: "0.4rem",
                              }}
                            >
                              <Star size={17} fill="#f59e0b" color="#f59e0b" />
                              Penilaian Kepuasan Penanganan Laporan
                            </div>
                            <p style={{ fontSize: "0.88rem", color: "#78350f", marginBottom: "0.75rem" }}>
                              Pilih tingkat kepuasan Anda terhadap hasil tindak lanjut petugas dinas:
                            </p>
                            <div
                              style={{
                                display: "flex",
                                flexWrap: "wrap",
                                gap: "0.5rem",
                                alignItems: "center",
                                marginBottom: "0.75rem",
                              }}
                            >
                              {[1, 2, 3, 4, 5].map((starVal) => {
                                const currentRating = getRatingDraft(report).rating;
                                const isSelected = starVal <= currentRating;
                                return (
                                  <button
                                    key={starVal}
                                    type="button"
                                    onClick={() => setRatingDraftField(report, "rating", starVal)}
                                    style={{
                                      display: "inline-flex",
                                      alignItems: "center",
                                      gap: "0.3rem",
                                      padding: "0.45rem 0.8rem",
                                      borderRadius: "8px",
                                      border: isSelected ? "2px solid #d97706" : "1px solid #cbd5e1",
                                      background: isSelected ? "#fef3c7" : "#ffffff",
                                      color: isSelected ? "#92400e" : "#475569",
                                      fontWeight: 700,
                                      fontSize: "0.9rem",
                                      cursor: "pointer",
                                    }}
                                    title={RATING_LABELS[starVal]}
                                  >
                                    <Star
                                      size={16}
                                      fill={isSelected ? "#f59e0b" : "none"}
                                      color={isSelected ? "#d97706" : "#94a3b8"}
                                    />
                                    {starVal}
                                  </button>
                                );
                              })}
                              <span
                                style={{
                                  fontSize: "0.9rem",
                                  fontWeight: 700,
                                  color: "#92400e",
                                  marginLeft: "0.35rem",
                                }}
                              >
                                {RATING_LABELS[getRatingDraft(report).rating] || ""}
                              </span>
                            </div>
                            <textarea
                              className="form-textarea"
                              rows={2}
                              maxLength={500}
                              placeholder="Tulis ulasan atau masukan singkat Anda terhadap penanganan petugas (opsional)..."
                              value={getRatingDraft(report).ulasan}
                              onChange={(e) => setRatingDraftField(report, "ulasan", e.target.value)}
                              style={{
                                background: "#ffffff",
                                fontSize: "0.9rem",
                                marginBottom: "0.75rem",
                              }}
                            />
                            <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
                              <button
                                type="button"
                                className="nav-btn nav-btn-primary"
                                disabled={submittingRatingId === report.id}
                                onClick={() => handleSubmitRating(report)}
                                style={{ padding: "0.5rem 1.1rem", fontSize: "0.88rem" }}
                              >
                                {submittingRatingId === report.id ? "Menyimpan..." : "Kirim Penilaian"}
                              </button>
                              {editingRatingId === report.id && (
                                <button
                                  type="button"
                                  className="nav-btn"
                                  onClick={() => setEditingRatingId(null)}
                                  style={{ padding: "0.5rem 0.9rem", fontSize: "0.85rem" }}
                                >
                                  Batal
                                </button>
                              )}
                            </div>
                          </div>
                        ) : report.rating_kepuasan ? (
                          <div>
                            <div
                              style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                flexWrap: "wrap",
                                gap: "0.5rem",
                              }}
                            >
                              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                                {[1, 2, 3, 4, 5].map((s) => (
                                  <Star
                                    key={s}
                                    size={16}
                                    fill={s <= report.rating_kepuasan ? "#f59e0b" : "none"}
                                    color={s <= report.rating_kepuasan ? "#d97706" : "#cbd5e1"}
                                  />
                                ))}
                                <strong style={{ fontSize: "0.9rem", color: "#92400e", marginLeft: "0.25rem" }}>
                                  {RATING_LABELS[report.rating_kepuasan] || `${report.rating_kepuasan}/5`}
                                </strong>
                              </div>
                              {userRole === "warga" && (
                                <button
                                  type="button"
                                  className="nav-btn"
                                  onClick={() => {
                                    setRatingDrafts((prev) => ({
                                      ...prev,
                                      [report.id]: {
                                        rating: report.rating_kepuasan,
                                        ulasan: report.ulasan_warga || "",
                                      },
                                    }));
                                    setEditingRatingId(report.id);
                                  }}
                                  style={{ padding: "0.25rem 0.65rem", fontSize: "0.78rem" }}
                                >
                                  Ubah Penilaian
                                </button>
                              )}
                            </div>
                            {report.ulasan_warga && (
                              <p
                                style={{
                                  margin: "0.45rem 0 0",
                                  fontSize: "0.9rem",
                                  color: "#78350f",
                                  lineHeight: 1.5,
                                }}
                              >
                                &ldquo;{report.ulasan_warga}&rdquo;
                              </p>
                            )}
                          </div>
                        ) : (
                          <div style={{ fontSize: "0.85rem", color: "#92400e" }}>
                            Belum ada penilaian kepuasan dari warga pelapor.
                          </div>
                        )}
                      </div>
                    )}

                    <div
                      className="report-card-meta"
                      style={{
                        fontSize: "0.85rem",
                        color: "var(--text-dim)",
                        display: "flex",
                        justifyContent: "space-between",
                        flexWrap: "wrap",
                        gap: "0.5rem",
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
                    {userRole === "warga" && (
                      <div className="report-card-actions" style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem", marginTop: "1rem" }}>
                        {report.status === "diterima" && (
                          <>
                            <button
                              type="button"
                              className="nav-btn"
                              onClick={() => openEditModal(report)}
                            >
                              Edit Pengaduan
                            </button>
                            <button
                              type="button"
                              className="nav-btn"
                              onClick={() => handleCancelReport(report.id)}
                              style={{ color: "#dc2626", borderColor: "#fecaca" }}
                            >
                              Batalkan Pengaduan
                            </button>
                          </>
                        )}
                        <button
                          type="button"
                          className="nav-btn"
                          onClick={() => handleViewAuditLogs(report)}
                          style={{ borderColor: "var(--accent-primary)", color: "var(--accent-primary)" }}
                        >
                          <Clock size={14} /> Riwayat Log
                        </button>
                      </div>
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
            className="glass-panel chat-panel-shell"
            style={{ maxWidth: "800px", margin: "0 auto" }}
          >
            <div
              className="chat-panel-header"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "0.75rem",
                marginBottom: "1.25rem",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
                <Bot size={32} className="text-accent-primary" style={{ flexShrink: 0 }} />
                <h2 style={{ fontSize: "clamp(1.3rem, 3.8vw, 1.75rem)", fontWeight: 800 }}>
                  Tanya AI GovSmart
                </h2>
              </div>
              <button
                type="button"
                className="nav-btn"
                onClick={handleClearChat}
                style={{ padding: "0.45rem 0.85rem", fontSize: "0.84rem", display: "inline-flex", alignItems: "center", gap: "0.4rem" }}
                title="Bersihkan riwayat percakapan di layar"
              >
                <RotateCcw size={14} /> Mulai Baru
              </button>
            </div>

            <div
              ref={chatContainerRef}
              className="chat-messages-box"
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
                  {msg.role === "ai" && msg.konteks_sebelumnya && (
                    <div
                      style={{
                        display: "inline-block",
                        marginBottom: "0.55rem",
                        padding: "0.2rem 0.6rem",
                        borderRadius: "6px",
                        background: "#eff6ff",
                        border: "1px solid #bfdbfe",
                        color: "#1e40af",
                        fontSize: "0.78rem",
                        fontWeight: 700,
                      }}
                    >
                      Melanjutkan topik: {msg.konteks_sebelumnya}
                    </div>
                  )}
                  {renderChatText(msg.text)}
                  {msg.role === "ai" && Array.isArray(msg.sumber) && msg.sumber.length > 0 && (
                    <div
                      style={{
                        marginTop: "0.75rem",
                        paddingTop: "0.6rem",
                        borderTop: "1px solid #e2e8f0",
                        fontSize: "0.8rem",
                        color: "#475569",
                      }}
                    >
                      <div style={{ fontWeight: 700, marginBottom: "0.3rem", color: "#334155" }}>
                        Sumber Dokumen Resmi:
                      </div>
                      <ul style={{ margin: 0, paddingLeft: "1.1rem", display: "flex", flexDirection: "column", gap: "0.2rem" }}>
                        {msg.sumber.map((s, sIdx) => (
                          <li key={sIdx}>
                            [{s.no}] {s.judul}
                            {s.konteks ? ` — ${s.konteks}` : ""}
                            {s.halaman ? ` (Hal. ${s.halaman})` : ""}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
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
              <div ref={chatEndRef} style={{ height: "1px" }} />
            </div>

            {/* Rekomendasi Pertanyaan Cepat */}
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginBottom: "1rem" }}>
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  type="button"
                  disabled={chatLoading}
                  onClick={() => sendChatMessage(qp)}
                  className="nav-btn"
                  style={{
                    padding: "0.35rem 0.75rem",
                    fontSize: "0.78rem",
                    background: "rgba(59, 130, 246, 0.06)",
                    borderColor: "rgba(59, 130, 246, 0.25)",
                    color: "var(--accent-primary)",
                    borderRadius: "999px",
                    cursor: chatLoading ? "not-allowed" : "pointer",
                    opacity: chatLoading ? 0.6 : 1,
                  }}
                >
                  {qp}
                </button>
              ))}
            </div>

            <form
              onSubmit={handleSendChat}
              className="chat-input-form"
            >
              <input
                ref={chatInputRef}
                type="text"
                maxLength={500}
                className="form-input"
                placeholder="Tanyakan panduan atau pertanyaan lanjutan (misal: Kalau biayanya berapa?)..."
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                style={{ flex: 1, minWidth: 0 }}
              />
              <button
                type="submit"
                disabled={chatLoading || !chatPrompt.trim()}
                className="nav-btn nav-btn-primary chat-send-btn"
              >
                <Send size={18} /> <span>{chatLoading ? "Mengirim..." : "Kirim"}</span>
              </button>
            </form>
          </div>
        )}

        {mainView === "admin" &&
          (userRole === "admin" || userRole === "super_admin") && (
            <div>
              <h1
                className="admin-page-title"
                style={{
                  fontSize: "clamp(1.4rem, 3.8vw, 2rem)",
                  fontWeight: 800,
                  marginBottom: "1.75rem",
                }}
              >
                Dasbor Manajemen & Penanganan Pengaduan
              </h1>

              {/* Kartu Ringkasan Statistik (KPI Metrics) */}
              <div className="kpi-grid">
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

                <div className="glass-panel" style={{ padding: "1.25rem 1.5rem", borderLeft: "4px solid #eab308" }}>
                  <div style={{ fontSize: "0.85rem", color: "#b45309", fontWeight: 700, display: "flex", alignItems: "center", gap: "0.35rem" }}>
                    <Star size={15} fill="#f59e0b" color="#d97706" /> Kepuasan Warga
                  </div>
                  <div style={{ fontSize: "2rem", fontWeight: 800, color: "#b45309", marginTop: "0.25rem" }}>
                    {kpiAvgRating ? (
                      <>
                        {kpiAvgRating} <span style={{ fontSize: "1rem", fontWeight: 600, color: "var(--text-muted)" }}>/ 5.0</span>
                      </>
                    ) : (
                      <span style={{ fontSize: "1.25rem", color: "var(--text-muted)" }}>Belum Ada</span>
                    )}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-dim)", marginTop: "0.25rem" }}>
                    {ratedReports.length > 0 ? `Dari ${ratedReports.length} penilaian warga` : "Menunggu penilaian warga"}
                  </div>
                </div>
              </div>
              {userRole === "super_admin" && (
                <div
                  className="glass-panel admin-dinas-banner"
                  style={{
                    padding: "1.25rem 1.75rem",
                    marginBottom: "2rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "1rem",
                    border: "1px solid rgba(59, 130, 246, 0.25)",
                    background: "rgba(255, 255, 255, 0.85)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    <div
                      style={{
                        width: "48px",
                        height: "48px",
                        borderRadius: "12px",
                        background: "rgba(59, 130, 246, 0.12)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <Users className="text-accent-primary" size={24} />
                    </div>
                    <div>
                      <h2 style={{ fontSize: "1.2rem", fontWeight: 800, margin: 0, color: "var(--text-main)" }}>
                        Daftar Admin Dinas
                      </h2>
                      <p style={{ margin: "0.25rem 0 0", fontSize: "0.88rem", color: "var(--text-muted)" }}>
                        Kelola data aparatur dan pendaftaran akun Admin OPD ({adminDinasList.length} akun terdaftar).
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="nav-btn nav-btn-primary admin-dinas-banner-btn"
                    onClick={() => setMainView("admin_dinas")}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.5rem",
                      padding: "0.75rem 1.4rem",
                      fontSize: "0.92rem",
                      fontWeight: 700,
                    }}
                  >
                    <Users size={18} />
                    Buka Halaman Daftar Admin Dinas &rarr;
                  </button>
                </div>
              )}

              {userRole === "super_admin" && (
                <div
                  className="glass-panel admin-dinas-banner"
                  style={{
                    padding: "1.25rem 1.75rem",
                    marginBottom: "2rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    flexWrap: "wrap",
                    gap: "1rem",
                    border: "1px solid rgba(16, 185, 129, 0.28)",
                    background: "rgba(255, 255, 255, 0.85)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    <div
                      style={{
                        width: "48px",
                        height: "48px",
                        borderRadius: "12px",
                        background: "rgba(16, 185, 129, 0.14)",
                        color: "#059669",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0,
                      }}
                    >
                      <User size={24} />
                    </div>
                    <div>
                      <h2 style={{ fontSize: "1.2rem", fontWeight: 800, margin: 0, color: "var(--text-main)" }}>
                        Daftar Akun User Warga
                      </h2>
                      <p style={{ margin: "0.25rem 0 0", fontSize: "0.88rem", color: "var(--text-muted)" }}>
                        Kelola data akun masyarakat terdaftar, edit profil, reset sandi, atau nonaktifkan akun ({wargaList.length} akun terdaftar).
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    className="nav-btn nav-btn-primary admin-dinas-banner-btn"
                    onClick={() => {
                      fetchWargaList(showInactiveWarga);
                      setMainView("user_warga");
                    }}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "0.5rem",
                      padding: "0.75rem 1.4rem",
                      fontSize: "0.92rem",
                      fontWeight: 700,
                    }}
                  >
                    <User size={18} />
                    Buka Halaman Daftar Akun Warga &rarr;
                  </button>
                </div>
              )}

              {/* Tab Pemisah Khusus Mode Mobile: Peta Sebaran vs Daftar Pengaduan */}
              <div className="admin-mobile-tabs" role="tablist" aria-label="Pilih tampilan dasbor">
                <button
                  type="button"
                  role="tab"
                  aria-selected={adminMobileTab === "peta"}
                  className={`admin-mobile-tab-btn ${adminMobileTab === "peta" ? "is-active" : ""}`}
                  onClick={() => setAdminMobileTab("peta")}
                >
                  <MapPin size={17} />
                  <span>Peta Sebaran ({mapFilteredReports.length})</span>
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={adminMobileTab === "daftar"}
                  className={`admin-mobile-tab-btn ${adminMobileTab === "daftar" ? "is-active" : ""}`}
                  onClick={() => setAdminMobileTab("daftar")}
                >
                  <FileText size={17} />
                  <span>Daftar Pengaduan ({filteredReports.length})</span>
                </button>
              </div>

              {/* Peta Lamongan dengan Pin Laporan */}
              <div
                className={`glass-panel admin-tab-panel ${adminMobileTab === "peta" ? "is-active-mobile-tab" : ""}`}
                style={{ padding: "1.5rem", marginBottom: "2rem" }}
              >
                <div className="admin-map-header">
                  <div>
                    <h2 style={{ fontSize: "1.18rem", fontWeight: 800, margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <MapPin className="text-accent-primary" style={{ flexShrink: 0 }} />
                      <span>Peta Sebaran Laporan — Kabupaten Lamongan</span>
                    </h2>
                    <p style={{ margin: "0.25rem 0 0", fontSize: "0.84rem", color: "var(--text-muted)" }}>
                      Menampilkan <strong>{mapFilteredReports.length}</strong> dari <strong>{allCoordReports.length}</strong> titik laporan berkoordinat GPS.
                    </p>
                  </div>

                  {/* Toggle Fokus Laporan Aktif vs Semua Status */}
                  <div className="map-status-toggle" role="group" aria-label="Filter status titik peta">
                    <button
                      type="button"
                      className={`map-status-pill ${mapStatusMode === "active" ? "is-active" : ""}`}
                      onClick={() => setMapStatusMode("active")}
                    >
                      Hanya Aktif ({activeCoordReportsByDept.length})
                    </button>
                    <button
                      type="button"
                      className={`map-status-pill ${mapStatusMode === "all" ? "is-active" : ""}`}
                      onClick={() => setMapStatusMode("all")}
                    >
                      Semua Status ({coordReportsByDept.length})
                    </button>
                  </div>
                </div>

                {/* Bar Kontrol Filter Dinas & Tombol Legenda Collapsible */}
                <div className="admin-map-toolbar">
                  <div className="admin-map-filter-select-wrap">
                    <Filter size={15} className="text-accent-primary" style={{ flexShrink: 0 }} />
                    <label htmlFor="map-dept-filter" className="admin-map-filter-label">
                      Filter Dinas:
                    </label>
                    <select
                      id="map-dept-filter"
                      className="form-select admin-map-select"
                      value={mapDeptFilter}
                      onChange={(e) => setMapDeptFilter(e.target.value)}
                    >
                      <option value="all">Semua Dinas ({allCoordReports.length} titik)</option>
                      {departments.map((d) => {
                        const deptCount = allCoordReports.filter(
                          (r) => Number(r.dept_id) === Number(d.id),
                        ).length;
                        return (
                          <option key={d.id} value={String(d.id)}>
                            {d.nama_dinas} ({deptCount})
                          </option>
                        );
                      })}
                    </select>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    {mapDeptFilter !== "all" && (
                      <button
                        type="button"
                        className="nav-btn map-legend-toggle-btn"
                        onClick={() => setMapDeptFilter("all")}
                      >
                        Reset Dinas
                      </button>
                    )}
                    <button
                      type="button"
                      className={`nav-btn map-legend-toggle-btn ${showMapLegend ? "is-open" : ""}`}
                      onClick={() => setShowMapLegend((prev) => !prev)}
                      aria-expanded={showMapLegend}
                    >
                      <span>{showMapLegend ? "Sembunyikan Legenda" : `Legenda Warna (${departments.length})`}</span>
                      <ChevronDown
                        size={15}
                        style={{
                          transform: showMapLegend ? "rotate(180deg)" : "rotate(0deg)",
                          transition: "transform 0.2s ease",
                        }}
                      />
                    </button>
                  </div>
                </div>

                {/* Legenda Dinas Collapsible (Tertutup secara default agar di Mobile tidak penuh) */}
                {showMapLegend && (
                  <div className="admin-map-legend-box">
                    {departments.map((d, i) => {
                      const isSelected = mapDeptFilter === String(d.id);
                      const deptCount = allCoordReports.filter(
                        (r) => Number(r.dept_id) === Number(d.id),
                      ).length;
                      return (
                        <button
                          key={d.id}
                          type="button"
                          onClick={() =>
                            setMapDeptFilter(isSelected ? "all" : String(d.id))
                          }
                          className={`admin-map-legend-chip ${isSelected ? "is-selected" : ""}`}
                          title="Klik untuk memfilter titik peta berdasarkan dinas ini"
                        >
                          <span
                            className="admin-map-legend-dot"
                            style={{ background: DEPT_COLORS[i % DEPT_COLORS.length] }}
                          />
                          <span>{d.nama_dinas.replace("Dinas ", "")}</span>
                          <span className="admin-map-legend-count">{deptCount}</span>
                        </button>
                      );
                    })}
                  </div>
                )}

                <div className="admin-map-box">
                  <MapContainer
                    center={[-7.1189, 112.4109]}
                    zoom={11}
                    style={{ height: "100%", width: "100%" }}
                    scrollWheelZoom={true}
                  >
                    <MapInvalidateSize
                      trigger={`${adminMobileTab}-${mapDeptFilter}-${mapStatusMode}`}
                    />
                    <TileLayer
                      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                      attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>'
                    />
                    {mapFilteredReports.map((r) => {
                      const deptIdx = departments.findIndex((d) => d.id === r.dept_id);
                      const color = DEPT_COLORS[deptIdx >= 0 ? deptIdx % DEPT_COLORS.length : 0];
                      return (
                        <Marker
                          key={r.id}
                          position={[parseFloat(r.lat), parseFloat(r.long)]}
                          icon={createReportIcon(color)}
                        >
                          <Popup>
                            <div style={{ minWidth: "200px", maxWidth: "250px" }}>
                              <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#64748b", marginBottom: "0.15rem" }}>
                                Laporan #{r.id}
                              </div>
                              <strong style={{ fontSize: "0.92rem", color: "#0d223a", display: "block", marginBottom: "0.25rem" }}>
                                {r.judul}
                              </strong>
                              <span style={{ fontSize: "0.8rem", color: "#475569", display: "block", marginBottom: "0.4rem" }}>
                                {departments.find((d) => d.id === r.dept_id)?.nama_dinas || "AI Auto-Routing"}
                              </span>
                              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem", marginBottom: "0.65rem", flexWrap: "wrap" }}>
                                <span
                                  style={{
                                    fontSize: "0.74rem",
                                    fontWeight: 800,
                                    color:
                                      r.urgensi === "darurat"
                                        ? "#ef4444"
                                        : r.urgensi === "penting"
                                        ? "#f97316"
                                        : "#16a34a",
                                  }}
                                >
                                  ● {r.urgensi.toUpperCase()}
                                </span>
                                <span style={{ color: "#cbd5e1" }}>|</span>
                                <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "#0e56a8", textTransform: "capitalize" }}>
                                  Status: {r.status}
                                </span>
                              </div>
                              <div style={{ display: "flex", gap: "0.4rem" }}>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setSelectedReport(r);
                                    setNewStatus(r.status);
                                    setCatatanPetugas(r.catatan_petugas || "");
                                  }}
                                  style={{
                                    flex: 1,
                                    padding: "0.38rem 0.6rem",
                                    borderRadius: "6px",
                                    border: "none",
                                    background: "#0e56a8",
                                    color: "#ffffff",
                                    fontSize: "0.76rem",
                                    fontWeight: 700,
                                    cursor: "pointer",
                                  }}
                                >
                                  Kelola Status
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleViewAuditLogs(r)}
                                  style={{
                                    padding: "0.38rem 0.6rem",
                                    borderRadius: "6px",
                                    border: "1px solid #0e56a8",
                                    background: "#ffffff",
                                    color: "#0e56a8",
                                    fontSize: "0.76rem",
                                    fontWeight: 700,
                                    cursor: "pointer",
                                  }}
                                >
                                  Log
                                </button>
                              </div>
                            </div>
                          </Popup>
                        </Marker>
                      );
                    })}
                  </MapContainer>
                </div>

                {mapFilteredReports.length === 0 && (
                  <div style={{ textAlign: "center", color: "var(--text-muted)", fontSize: "0.86rem", marginTop: "0.85rem", display: "flex", flexDirection: "column", alignItems: "center", gap: "0.45rem" }}>
                    <span>
                      {allCoordReports.length === 0
                        ? "Belum ada laporan dengan data koordinat lokasi."
                        : mapStatusMode === "active" && coordReportsByDept.length > 0
                        ? `Tidak ada laporan aktif (Diterima/Diproses) pada filter ini, namun ada ${coordReportsByDept.length} laporan selesai/ditolak.`
                        : "Tidak ada titik laporan untuk filter dinas yang dipilih."}
                    </span>
                    {mapStatusMode === "active" && coordReportsByDept.length > 0 && (
                      <button
                        type="button"
                        className="nav-btn"
                        style={{ padding: "0.35rem 0.85rem", fontSize: "0.8rem", borderColor: "var(--accent-primary)", color: "var(--accent-primary)" }}
                        onClick={() => setMapStatusMode("all")}
                      >
                        Tampilkan Semua Status ({coordReportsByDept.length} titik)
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div
                className={`glass-panel admin-tab-panel ${adminMobileTab === "daftar" ? "is-active-mobile-tab" : ""}`}
                style={{ padding: "1.5rem" }}
              >
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
                  {["all", "diterima", "diproses", "selesai", "ditolak", "dibatalkan"].map((s) => (
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
                  <div className="table-responsive-wrap">
                    <table
                      className="responsive-table"
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
                            {r.rating_kepuasan && (
                              <div
                                style={{
                                  marginTop: "0.3rem",
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: "0.25rem",
                                  padding: "0.15rem 0.5rem",
                                  borderRadius: "6px",
                                  background: "#fef3c7",
                                  border: "1px solid #fde68a",
                                  color: "#92400e",
                                  fontSize: "0.78rem",
                                  fontWeight: 700,
                                }}
                                title={r.ulasan_warga ? `Ulasan warga: "${r.ulasan_warga}"` : RATING_LABELS[r.rating_kepuasan]}
                              >
                                <Star size={12} fill="#f59e0b" color="#d97706" />
                                {r.rating_kepuasan}/5
                              </div>
                            )}
                          </td>
                          <td
                            style={{
                              padding: "1rem",
                              display: "flex",
                              gap: "0.5rem",
                              flexWrap: "wrap",
                            }}
                          >
                            <button
                              className="nav-btn"
                              style={{
                                padding: "0.4rem 0.8rem",
                                fontSize: "0.85rem",
                                whiteSpace: "nowrap",
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
                                whiteSpace: "nowrap",
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
                </div>
              )}
            </div>
          </div>
        )}

        {mainView === "admin_dinas" && userRole === "super_admin" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div
              className="glass-panel"
              style={{
                padding: "1.5rem 2rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <div>
                <h1 style={{ fontSize: "clamp(1.35rem, 3.5vw, 1.75rem)", fontWeight: 800, margin: 0 }}>
                  Manajemen Admin Dinas (OPD)
                </h1>
                <p style={{ color: "var(--text-muted)", margin: "0.4rem 0 0", fontSize: "0.95rem" }}>
                  Kelola hak akses dan pendaftaran akun aparatur dinas untuk seluruh Organisasi Perangkat Daerah Kabupaten Lamongan.
                </p>
              </div>
              <button
                type="button"
                className="nav-btn"
                onClick={() => setMainView("admin")}
                style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}
              >
                &larr; Kembali ke Dasbor Admin
              </button>
            </div>

            {/* Registrasi Akun Admin Dinas Baru */}
            <div className="glass-panel" style={{ padding: "2rem" }}>
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
                <UserPlus className="text-accent-primary" /> Registrasi Akun Admin Dinas Baru
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
                className="admin-create-grid"
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
                  className="nav-btn nav-btn-primary admin-create-submit"
                  style={{ padding: "0.85rem 1.5rem", justifyContent: "center" }}
                >
                  Buat Akun
                </button>
              </form>
            </div>

            {/* Daftar Admin Dinas Terdaftar */}
            <div className="glass-panel" style={{ padding: "1.5rem" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "1rem",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                }}
              >
                <h2
                  style={{
                    fontSize: "1.2rem",
                    fontWeight: 700,
                    margin: 0,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Users className="text-accent-primary" /> Daftar Admin Dinas Terdaftar (
                  {filteredAdminDinas.length}
                  {filteredAdminDinas.length !== adminDinasList.length
                    ? ` dari ${adminDinasList.length}`
                    : ""}
                  )
                </h2>
                <div style={{ display: "flex", alignItems: "center", gap: "0.65rem", flexWrap: "wrap" }}>
                  <label
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      fontSize: "0.82rem",
                      fontWeight: 600,
                      color: "var(--text-main)",
                      cursor: "pointer",
                      padding: "0.35rem 0.7rem",
                      borderRadius: "8px",
                      background: showInactiveAdmins ? "#eff6ff" : "#f8fafc",
                      border: "1px solid var(--border-color)",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={showInactiveAdmins}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setShowInactiveAdmins(checked);
                        fetchAdminDinas(checked);
                      }}
                    />
                    <span>Tampilkan Akun Non-aktif</span>
                  </label>
                  <button
                    type="button"
                    className="nav-btn"
                    onClick={() => fetchAdminDinas(showInactiveAdmins)}
                    style={{ fontSize: "0.82rem", padding: "0.35rem 0.8rem" }}
                  >
                    Segarkan Data
                  </button>
                </div>
              </div>

              {/* Filter Berdasarkan Nama Dinas & Pencarian Cepat */}
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.85rem",
                  alignItems: "center",
                  marginBottom: "1.25rem",
                  padding: "0.9rem 1rem",
                  background: "#f8fafc",
                  borderRadius: "10px",
                  border: "1px solid var(--border-color)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flex: "1 1 280px" }}>
                  <Filter size={16} className="text-accent-primary" style={{ flexShrink: 0 }} />
                  <label
                    htmlFor="filter-admin-dinas"
                    style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--text-main)", whiteSpace: "nowrap" }}
                  >
                    Filter Dinas:
                  </label>
                  <select
                    id="filter-admin-dinas"
                    className="form-select"
                    value={adminDeptFilter}
                    onChange={(e) => setAdminDeptFilter(e.target.value)}
                    style={{ padding: "0.5rem 0.85rem", fontSize: "0.9rem" }}
                  >
                    <option value="all">Semua Dinas ({adminDinasList.length})</option>
                    {departments.map((d) => {
                      const count = adminDinasList.filter((a) => Number(a.dept_id) === Number(d.id)).length;
                      return (
                        <option key={d.id} value={String(d.id)}>
                          {d.nama_dinas} ({count})
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div style={{ position: "relative", flex: "1 1 240px" }}>
                  <Search
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "var(--text-muted)",
                    }}
                  />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Cari nama dinas, NIP, atau email..."
                    value={adminSearchQuery}
                    onChange={(e) => setAdminSearchQuery(e.target.value)}
                    style={{ padding: "0.5rem 0.85rem 0.5rem 2.2rem", fontSize: "0.9rem" }}
                  />
                </div>

                {(adminDeptFilter !== "all" || adminSearchQuery.trim() !== "") && (
                  <button
                    type="button"
                    className="nav-btn"
                    onClick={() => {
                      setAdminDeptFilter("all");
                      setAdminSearchQuery("");
                    }}
                    style={{ padding: "0.45rem 0.85rem", fontSize: "0.84rem", borderColor: "var(--border-color)" }}
                  >
                    Reset Filter
                  </button>
                )}
              </div>

              {filteredAdminDinas.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "0.92rem", padding: "1rem 0" }}>
                  {adminDinasList.length === 0
                    ? "Belum ada Admin Dinas terdaftar."
                    : "Tidak ada akun Admin Dinas yang sesuai dengan filter dinas atau kata kunci yang dipilih."}
                </p>
              ) : (
                <div className="table-responsive-wrap">
                  <table className="responsive-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
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
                      {filteredAdminDinas.map((a) => (
                        <tr key={a.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                          <td style={{ padding: "0.75rem", fontWeight: 600 }}>#{a.id}</td>
                          <td style={{ padding: "0.75rem" }}>{a.nik_or_nip}</td>
                          <td style={{ padding: "0.75rem" }}>{a.email}</td>
                          <td style={{ padding: "0.75rem" }}>{a.nama_dinas || departments.find((d) => d.id === a.dept_id)?.nama_dinas || "-"}</td>
                          <td style={{ padding: "0.75rem" }}>
                            <span
                              style={{
                                display: "inline-block",
                                padding: "0.2rem 0.55rem",
                                borderRadius: "999px",
                                fontSize: "0.75rem",
                                fontWeight: 700,
                                background: a.is_active ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                                color: a.is_active ? "#059669" : "#dc2626",
                              }}
                            >
                              {a.is_active ? "Aktif" : "Non-aktif"}
                            </span>
                          </td>
                          <td style={{ padding: "0.75rem", display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                            <button
                              className="nav-btn"
                              style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem" }}
                              onClick={() => handleEditAdminDinas(a)}
                            >
                              Edit
                            </button>
                            {a.is_active ? (
                              <button
                                className="nav-btn"
                                style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#ef4444", color: "#ef4444" }}
                                onClick={() => handleDeleteAdminDinas(a, false)}
                              >
                                Nonaktifkan
                              </button>
                            ) : (
                              <>
                                <button
                                  className="nav-btn"
                                  style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#059669", color: "#059669" }}
                                  onClick={() => handleActivateAdminDinas(a)}
                                >
                                  Aktifkan
                                </button>
                                <button
                                  className="nav-btn"
                                  style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#dc2626", color: "#dc2626" }}
                                  onClick={() => handleDeleteAdminDinas(a, true)}
                                >
                                  Hapus Permanen
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {mainView === "user_warga" && userRole === "super_admin" && (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div
              className="glass-panel"
              style={{
                padding: "1.5rem 2rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: "1rem",
              }}
            >
              <div>
                <h1 style={{ fontSize: "clamp(1.35rem, 3.5vw, 1.75rem)", fontWeight: 800, margin: 0 }}>
                  Manajemen Akun User Warga
                </h1>
                <p style={{ color: "var(--text-muted)", margin: "0.4rem 0 0", fontSize: "0.95rem" }}>
                  Kelola daftar akun masyarakat & pelaku UMKM Kabupaten Lamongan yang terdaftar di portal GovSmart.
                </p>
              </div>
              <button
                type="button"
                className="nav-btn"
                onClick={() => setMainView("admin")}
                style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}
              >
                &larr; Kembali ke Dasbor Admin
              </button>
            </div>

            <div className="glass-panel" style={{ padding: "1.5rem" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "1rem",
                  flexWrap: "wrap",
                  gap: "0.75rem",
                }}
              >
                <h2
                  style={{
                    fontSize: "1.2rem",
                    fontWeight: 700,
                    margin: 0,
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <User className="text-accent-primary" /> Daftar Akun Warga Terdaftar (
                  {filteredWargaList.length}
                  {filteredWargaList.length !== wargaList.length
                    ? ` dari ${wargaList.length}`
                    : ""}
                  )
                </h2>
                <div style={{ display: "flex", alignItems: "center", gap: "0.65rem", flexWrap: "wrap" }}>
                  <label
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.4rem",
                      fontSize: "0.82rem",
                      fontWeight: 600,
                      color: "var(--text-main)",
                      cursor: "pointer",
                      padding: "0.35rem 0.7rem",
                      borderRadius: "8px",
                      background: showInactiveWarga ? "#eff6ff" : "#f8fafc",
                      border: "1px solid var(--border-color)",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={showInactiveWarga}
                      onChange={(e) => {
                        const checked = e.target.checked;
                        setShowInactiveWarga(checked);
                        fetchWargaList(checked);
                      }}
                    />
                    <span>Tampilkan Akun Non-aktif</span>
                  </label>
                  <button
                    type="button"
                    className="nav-btn"
                    onClick={() => fetchWargaList(showInactiveWarga)}
                    style={{ fontSize: "0.82rem", padding: "0.35rem 0.8rem" }}
                  >
                    Segarkan Data
                  </button>
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.85rem",
                  alignItems: "center",
                  marginBottom: "1.25rem",
                  padding: "0.9rem 1rem",
                  background: "#f8fafc",
                  borderRadius: "10px",
                  border: "1px solid var(--border-color)",
                }}
              >
                <div style={{ position: "relative", flex: "1 1 280px" }}>
                  <Search
                    size={15}
                    style={{
                      position: "absolute",
                      left: "12px",
                      top: "50%",
                      transform: "translateY(-50%)",
                      color: "var(--text-muted)",
                    }}
                  />
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Cari nama warga, NIK, email, atau nomor telepon..."
                    value={wargaSearchQuery}
                    onChange={(e) => setWargaSearchQuery(e.target.value)}
                    style={{ padding: "0.5rem 0.85rem 0.5rem 2.2rem", fontSize: "0.9rem" }}
                  />
                </div>
                {wargaSearchQuery.trim() !== "" && (
                  <button
                    type="button"
                    className="nav-btn"
                    onClick={() => setWargaSearchQuery("")}
                    style={{ padding: "0.45rem 0.85rem", fontSize: "0.84rem", borderColor: "var(--border-color)" }}
                  >
                    Reset Pencarian
                  </button>
                )}
              </div>

              {filteredWargaList.length === 0 ? (
                <p style={{ color: "var(--text-muted)", fontSize: "0.92rem", padding: "1rem 0" }}>
                  {wargaList.length === 0
                    ? "Belum ada akun warga terdaftar."
                    : "Tidak ada akun warga yang cocok dengan kata kunci pencarian."}
                </p>
              ) : (
                <div className="table-responsive-wrap">
                  <table className="responsive-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid var(--border-color)", textAlign: "left", color: "var(--text-muted)" }}>
                        <th style={{ padding: "0.75rem" }}>ID</th>
                        <th style={{ padding: "0.75rem" }}>NIK</th>
                        <th style={{ padding: "0.75rem" }}>Nama Lengkap</th>
                        <th style={{ padding: "0.75rem" }}>Email</th>
                        <th style={{ padding: "0.75rem" }}>No. Telepon</th>
                        <th style={{ padding: "0.75rem" }}>Status</th>
                        <th style={{ padding: "0.75rem" }}>Aksi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredWargaList.map((w) => (
                        <tr key={w.id} style={{ borderBottom: "1px solid #e2e8f0" }}>
                          <td style={{ padding: "0.75rem", fontWeight: 600 }}>#{w.id}</td>
                          <td style={{ padding: "0.75rem" }}>{w.nik_or_nip}</td>
                          <td style={{ padding: "0.75rem" }}>{w.nama_lengkap || "-"}</td>
                          <td style={{ padding: "0.75rem" }}>{w.email}</td>
                          <td style={{ padding: "0.75rem" }}>{w.no_telepon || "-"}</td>
                          <td style={{ padding: "0.75rem" }}>
                            <span
                              style={{
                                display: "inline-block",
                                padding: "0.2rem 0.55rem",
                                borderRadius: "999px",
                                fontSize: "0.75rem",
                                fontWeight: 700,
                                background: w.is_active ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                                color: w.is_active ? "#059669" : "#dc2626",
                              }}
                            >
                              {w.is_active ? "Aktif" : "Non-aktif"}
                            </span>
                          </td>
                          <td style={{ padding: "0.75rem", display: "flex", gap: "0.35rem", flexWrap: "wrap" }}>
                            <button
                              className="nav-btn"
                              style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem" }}
                              onClick={() => handleEditWarga(w)}
                            >
                              Edit
                            </button>
                            {w.is_active ? (
                              <button
                                className="nav-btn"
                                style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#ef4444", color: "#ef4444" }}
                                onClick={() => handleDeleteWarga(w, false)}
                              >
                                Nonaktifkan
                              </button>
                            ) : (
                              <>
                                <button
                                  className="nav-btn"
                                  style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#059669", color: "#059669" }}
                                  onClick={() => handleActivateWarga(w)}
                                >
                                  Aktifkan
                                </button>
                                <button
                                  className="nav-btn"
                                  style={{ padding: "0.3rem 0.7rem", fontSize: "0.8rem", borderColor: "#dc2626", color: "#dc2626" }}
                                  onClick={() => handleDeleteWarga(w, true)}
                                >
                                  Hapus Permanen
                                </button>
                              </>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modals for Admin Actions */}
      {selectedReport && !showAuditModal && (
        <div
          className="modal-overlay"
          onClick={() => {
            setSelectedReport(null);
            setCatatanPetugas("");
            setFeedbackFile(null);
            setFeedbackUploadMsg("");
          }}
        >
          <div
            className="modal-content status-update-modal"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header Modal */}
            <div className="status-modal-header">
              <div className="status-modal-title-group">
                <div className="status-modal-icon-badge">
                  <FileText size={20} />
                </div>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                    <h3 className="status-modal-title">
                      Pembaruan Status Laporan #{selectedReport.id}
                    </h3>
                    <span className={`badge badge-${selectedReport.urgensi}`} style={{ fontSize: "0.7rem", padding: "0.2rem 0.6rem" }}>
                      {selectedReport.urgensi}
                    </span>
                  </div>
                  <p className="status-modal-subtitle">
                    <Building2 size={13} style={{ display: "inline", marginRight: "4px", verticalAlign: "-2px" }} />
                    {departments.find((d) => d.id === selectedReport.dept_id)?.nama_dinas || "AI Auto-Routing"}
                  </p>
                </div>
              </div>
              <button
                type="button"
                className="status-modal-close-btn"
                aria-label="Tutup modal"
                onClick={() => {
                  setSelectedReport(null);
                  setCatatanPetugas("");
                  setFeedbackFile(null);
                  setFeedbackUploadMsg("");
                }}
              >
                <X size={19} />
              </button>
            </div>

            {/* Kartu Ringkasan Laporan Warga */}
            <div className="status-modal-report-card">
              <div className="status-modal-section-kicker">DETAIL LAPORAN WARGA</div>
              <h4 className="status-modal-report-heading">{selectedReport.judul}</h4>
              {selectedReport.isi_laporan &&
                selectedReport.isi_laporan.trim() !== selectedReport.judul?.trim() && (
                  <p className="status-modal-report-body">{selectedReport.isi_laporan}</p>
                )}

              {(selectedReport.lat && selectedReport.long) || selectedReport.foto_bukti ? (
                <div className="status-modal-report-meta">
                  {selectedReport.lat && selectedReport.long && (
                    <a
                      href={`https://www.google.com/maps?q=${selectedReport.lat},${selectedReport.long}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="status-modal-gps-chip"
                    >
                      <MapPin size={13} />
                      <span>Lokasi GPS ({selectedReport.lat}, {selectedReport.long})</span>
                    </a>
                  )}
                </div>
              ) : null}

              {selectedReport.foto_bukti && (
                <div style={{ marginTop: "0.75rem" }}>
                  <p style={{ fontSize: "0.76rem", fontWeight: 700, color: "#486581", marginBottom: "0.35rem" }}>
                    Foto Bukti Lampiran Warga:
                  </p>
                  <img
                    src={apiUrl(`/uploads/${selectedReport.foto_bukti}`)}
                    alt="Foto Bukti"
                    style={{
                      width: "100%",
                      maxHeight: "170px",
                      borderRadius: "10px",
                      objectFit: "cover",
                      border: "1px solid var(--border-color)",
                      cursor: "pointer",
                    }}
                    onClick={() => window.open(apiUrl(`/uploads/${selectedReport.foto_bukti}`), "_blank")}
                    title="Klik untuk membuka ukuran penuh"
                  />
                </div>
              )}
            </div>

            {/* Penilaian Warga (Jika sudah ada) */}
            {selectedReport.rating_kepuasan && (
              <div
                style={{
                  marginBottom: "1.15rem",
                  padding: "0.85rem 1rem",
                  background: "#fffbeb",
                  border: "1px solid #fde68a",
                  borderLeft: "4px solid #f59e0b",
                  borderRadius: "10px",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: "0.35rem", marginBottom: "0.2rem", flexWrap: "wrap" }}>
                  {[1, 2, 3, 4, 5].map((s) => (
                    <Star
                      key={s}
                      size={15}
                      fill={s <= selectedReport.rating_kepuasan ? "#f59e0b" : "none"}
                      color={s <= selectedReport.rating_kepuasan ? "#d97706" : "#cbd5e1"}
                    />
                  ))}
                  <strong style={{ fontSize: "0.86rem", color: "#92400e", marginLeft: "0.25rem" }}>
                    Penilaian Warga: {RATING_LABELS[selectedReport.rating_kepuasan] || `${selectedReport.rating_kepuasan}/5`}
                  </strong>
                </div>
                {selectedReport.ulasan_warga && (
                  <p style={{ margin: "0.25rem 0 0", fontSize: "0.86rem", color: "#78350f" }}>
                    &ldquo;{selectedReport.ulasan_warga}&rdquo;
                  </p>
                )}
              </div>
            )}

            {/* Pemilih Status Baru Interaktif (4 Kartu Pill Status) */}
            <div className="form-group" style={{ marginBottom: "1.15rem" }}>
              <label className="form-label" style={{ fontSize: "0.92rem", marginBottom: "0.35rem" }}>
                Pilih Status Baru
              </label>
              <div className="status-selector-grid" role="radiogroup" aria-label="Pilih status laporan">
                {[
                  { value: "diterima", label: "Diterima", desc: "Laporan masuk", icon: FileText, tone: "blue" },
                  { value: "diproses", label: "Diproses", desc: "Ditindaklanjuti", icon: Clock, tone: "amber" },
                  { value: "selesai", label: "Selesai", desc: "Penanganan tuntas", icon: CheckCircle, tone: "emerald" },
                  { value: "ditolak", label: "Ditolak", desc: "Tidak valid", icon: X, tone: "rose" },
                ].map((opt) => {
                  const IconComp = opt.icon;
                  const active = newStatus === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      role="radio"
                      aria-checked={active}
                      onClick={() => setNewStatus(opt.value)}
                      className={`status-option-card tone-${opt.tone} ${active ? "is-selected" : ""}`}
                    >
                      <span className="status-option-icon">
                        <IconComp size={16} />
                      </span>
                      <span className="status-option-text">
                        <strong>{opt.label}</strong>
                        <small>{opt.desc}</small>
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Catatan / Tindak Lanjut Petugas */}
            <div className="form-group" style={{ marginBottom: "1.15rem" }}>
              <label className="form-label" style={{ fontSize: "0.92rem" }}>
                Catatan / Tindak Lanjut Petugas <span style={{ fontWeight: 500, color: "#64748b", fontSize: "0.82rem" }}>(Opsional)</span>
              </label>
              <textarea
                className="form-input status-modal-textarea"
                rows={3}
                placeholder="Tuliskan keterangan perbaikan, tindak lanjut tim lapangan, atau alasan penolakan..."
                value={catatanPetugas}
                onChange={(e) => setCatatanPetugas(e.target.value)}
              />
            </div>

            {/* Bagian Dokumen / Foto Feedback Dinas */}
            <div className="status-modal-feedback-box">
              <div className="status-modal-feedback-header">
                <span className="form-label" style={{ fontSize: "0.9rem", margin: 0 }}>
                  Lampiran Bukti Tindak Lanjut Dinas <span style={{ fontWeight: 500, color: "#64748b", fontSize: "0.8rem" }}>(Opsional)</span>
                </span>
              </div>

              {/* Preview dokumen feedback jika sudah ada */}
              {selectedReport.foto_feedback && (
                <div className="feedback-existing-card">
                  <div className="feedback-existing-info">
                    <span className="feedback-existing-badge">
                      <FileText size={16} />
                    </span>
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#0d223a" }}>
                        Dokumen Feedback Terlampir
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#486581", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {selectedReport.foto_feedback.toLowerCase().endsWith(".pdf")
                          ? "Dokumen PDF Resmi"
                          : "Foto Bukti Penanganan"}
                      </div>
                    </div>
                  </div>
                  {selectedReport.foto_feedback.toLowerCase().endsWith(".pdf") ? (
                    <a
                      href={apiUrl("/uploads/" + selectedReport.foto_feedback)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="feedback-open-doc-btn"
                    >
                      Buka PDF &rarr;
                    </a>
                  ) : (
                    <button
                      type="button"
                      className="feedback-open-doc-btn"
                      onClick={() => window.open(apiUrl("/uploads/" + selectedReport.foto_feedback), "_blank")}
                    >
                      Lihat Foto &rarr;
                    </button>
                  )}
                </div>
              )}

              {/* Form Upload Dokumen/Foto Feedback Modern */}
              <form onSubmit={handleUploadFeedback} className="feedback-upload-form">
                <input
                  id="feedback-file-picker"
                  type="file"
                  accept="image/jpeg,image/png,image/webp,application/pdf"
                  onChange={(e) => {
                    setFeedbackFile(e.target.files[0] || null);
                    setFeedbackUploadMsg("");
                  }}
                  style={{ display: "none" }}
                />
                <div className="feedback-picker-row">
                  <label htmlFor="feedback-file-picker" className="feedback-file-trigger">
                    <Download size={15} style={{ transform: "rotate(180deg)", flexShrink: 0 }} />
                    <span className="feedback-file-name">
                      {feedbackFile ? feedbackFile.name : "Pilih File PDF / Foto (Maks 5MB)..."}
                    </span>
                  </label>
                  <button
                    type="submit"
                    className={`nav-btn feedback-upload-submit-btn ${feedbackFile ? "is-ready" : ""}`}
                    disabled={feedbackUploading || !feedbackFile}
                  >
                    {feedbackUploading ? "Mengupload..." : "Upload"}
                  </button>
                </div>
                {feedbackUploadMsg && (
                  <p
                    style={{
                      fontSize: "0.8rem",
                      marginTop: "0.45rem",
                      color: feedbackUploadMsg.startsWith("✅") ? "#059669" : "#dc2626",
                      fontWeight: 700,
                    }}
                  >
                    {feedbackUploadMsg}
                  </p>
                )}
              </form>
            </div>

            {/* Footer Aksi Modal */}
            <div className="status-modal-footer">
              <button
                type="button"
                className="nav-btn status-modal-cancel-btn"
                onClick={() => {
                  setSelectedReport(null);
                  setCatatanPetugas("");
                  setFeedbackFile(null);
                  setFeedbackUploadMsg("");
                }}
              >
                Batal
              </button>
              <button
                type="button"
                className="nav-btn nav-btn-primary status-modal-save-btn"
                onClick={() => handleUpdateStatus(selectedReport.id)}
              >
                <CheckCircle size={17} />
                <span>Simpan Perubahan</span>
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
                    {log.admin_id ? `Oleh Petugas Admin (#${log.admin_id})` : "Oleh Sistem AI GovSmart / Pelapor"} &bull;{" "}
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

      {/* Edit Akun Warga Modal */}
      {editingWarga && (
        <div className="modal-overlay" onClick={() => setEditingWarga(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: "480px" }}>
            <h3 style={{ fontSize: "1.25rem", fontWeight: 800, marginBottom: "1rem" }}>
              Edit Akun Warga — #{editingWarga.id}
            </h3>
            <form onSubmit={handleUpdateWarga}>
              <div className="form-group">
                <label className="form-label">NIK KTP (Tidak dapat diubah)</label>
                <input
                  type="text"
                  className="form-input"
                  value={editingWarga.nik_or_nip || "-"}
                  disabled
                  readOnly
                  style={{ background: "#f1f5f9", color: "#64748b", cursor: "not-allowed" }}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Nama Lengkap</label>
                <input
                  type="text"
                  className="form-input"
                  maxLength={120}
                  value={editWargaForm.nama_lengkap}
                  onChange={(e) => setEditWargaForm({ ...editWargaForm, nama_lengkap: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Alamat Email</label>
                <input
                  type="email"
                  className="form-input"
                  required
                  value={editWargaForm.email}
                  onChange={(e) => setEditWargaForm({ ...editWargaForm, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">No. Telepon / WhatsApp</label>
                <input
                  type="tel"
                  className="form-input"
                  maxLength={30}
                  value={editWargaForm.no_telepon}
                  onChange={(e) => setEditWargaForm({ ...editWargaForm, no_telepon: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Alamat Domisili</label>
                <input
                  type="text"
                  className="form-input"
                  maxLength={255}
                  value={editWargaForm.alamat}
                  onChange={(e) => setEditWargaForm({ ...editWargaForm, alamat: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Password Baru (kosongkan jika tidak diubah)</label>
                <input
                  type="password"
                  className="form-input"
                  placeholder="••••••••"
                  value={editWargaForm.password}
                  onChange={(e) => setEditWargaForm({ ...editWargaForm, password: e.target.value })}
                />
              </div>
              <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end", marginTop: "1.5rem" }}>
                <button className="nav-btn" type="button" onClick={() => setEditingWarga(null)}>
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
        <div className="modal-overlay">
          <div className="modal-content">
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
              <div className="coord-grid" style={{ marginBottom: "1rem" }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Latitude (Opsional)</label>
                  <input type="number" step="any" className="form-input" value={editLat} onChange={(e) => setEditLat(e.target.value)} />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                  <label className="form-label">Longitude (Opsional)</label>
                  <input type="number" step="any" className="form-input" value={editLong} onChange={(e) => setEditLong(e.target.value)} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Ganti / Tambah Foto Bukti (Opsional, JPEG/PNG/WEBP, maks 5 MB)</label>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="form-input"
                  onChange={(e) => setEditFotoFile(e.target.files?.[0] || null)}
                />
                {editReportModal.report?.foto_bukti && !editFotoFile && (
                  <small style={{ color: "var(--text-muted)", display: "block", marginTop: "0.3rem" }}>
                    Foto saat ini sudah terlampir. Pilih file baru hanya jika ingin mengganti foto bukti.
                  </small>
                )}
              </div>
              <div style={{ marginTop: 20, display: "flex", justifyContent: "flex-end", flexWrap: "wrap", gap: 12 }}>
                <button type="button" className="nav-btn" onClick={() => setEditReportModal({ open: false, report: null })}>Batal</button>
                <button type="submit" className="nav-btn nav-btn-primary" disabled={editUploadingFoto}>
                  {editUploadingFoto ? "Mengunggah Foto..." : "Simpan Perubahan"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
