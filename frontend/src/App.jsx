import React, { useState, useEffect } from 'react';
import { 
  Building2, MessageSquare, AlertTriangle, ShieldCheck, LogIn, LogOut, 
  Send, UserPlus, MapPin, CheckCircle, Clock, FileText, Bot, X, Sparkles, Filter, Search
} from 'lucide-react';

export default function App() {
  const [mainView, setMainView] = useState('options'); // 'options' | 'pengaduan' | 'pertanyaan' | 'admin'
  const [token, setToken] = useState(localStorage.getItem('govsmart_token') || '');
  const [userRole, setUserRole] = useState(localStorage.getItem('govsmart_role') || '');
  const [userEmail, setUserEmail] = useState(localStorage.getItem('govsmart_email') || '');
  
  // Auth Modal State
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [regNik, setRegNik] = useState('');
  const [authError, setAuthError] = useState('');

  // Warga Form State
  const [judul, setJudul] = useState('');
  const [isiLaporan, setIsiLaporan] = useState('');
  const [lat, setLat] = useState('');
  const [long, setLong] = useState('');
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Reports Data State
  const [reports, setReports] = useState([]);
  const [loadingReports, setLoadingReports] = useState(false);
  const [departments, setDepartments] = useState([]);

  // Admin Audit & Update Modal State
  const [selectedReport, setSelectedReport] = useState(null);
  const [newStatus, setNewStatus] = useState('');
  const [auditLogs, setAuditLogs] = useState([]);
  const [showAuditModal, setShowAuditModal] = useState(false);

  // Super Admin Register State
  const [adminNip, setAdminNip] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [adminSuccess, setAdminSuccess] = useState('');

  // AI Chatbot Widget State
  const [showChatbot, setShowChatbot] = useState(false);
  const [chatPrompt, setChatPrompt] = useState('');
  const [chatMessages, setChatMessages] = useState([
    { role: 'ai', text: 'Halo! Saya Asisten AI GovSmart. Ada yang bisa saya bantu terkait perizinan UMKM/NIB atau panduan layanan publik?' }
  ]);
  const [chatLoading, setChatLoading] = useState(false);

  // Fetch Reports & Departments
  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const res = await fetch('/api/v1/reports/', { headers });
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
      const res = await fetch('/api/v1/departments/');
      if (res.ok) {
        const data = await res.json();
        setDepartments(data);
      }
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchReports();
    fetchDepartments();
  }, [token]);

  // Auth Handlers
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const formData = new URLSearchParams();
      formData.append('username', loginEmail);
      formData.append('password', loginPassword);

      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });

      if (!res.ok) {
        const err = await res.json();
        let errorMsg = 'Login gagal';
        if (typeof err.detail === 'string') {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map(d => d.msg).join(', ');
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      localStorage.setItem('govsmart_token', data.access_token);
      setToken(data.access_token);
      
      // Determine user role via /me
      const profileRes = await fetch('/api/v1/admin/me', {
        headers: { 'Authorization': `Bearer ${data.access_token}` }
      });
      if (profileRes.ok) {
        const profile = await profileRes.json();
        localStorage.setItem('govsmart_role', profile.role);
        localStorage.setItem('govsmart_email', profile.email);
        setUserRole(profile.role);
        setUserEmail(profile.email);
      }

      setMainView('options');
    } catch (e) {
      setAuthError(e.message);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const res = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: loginEmail,
          nik_or_nip: regNik,
          password: loginPassword
        })
      });

      if (!res.ok) {
        const err = await res.json();
        let errorMsg = 'Registrasi gagal';
        if (typeof err.detail === 'string') {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map(d => {
            let msg = d.msg;
            if (msg.includes('String should have at least')) {
              const num = msg.match(/\d+/)?.[0] || 'beberapa';
              msg = `Minimal ${num} karakter.`;
            } else if (msg.includes('String should have at most')) {
              const num = msg.match(/\d+/)?.[0] || 'tertentu';
              msg = `Maksimal ${num} karakter.`;
            } else if (msg.includes('value is not a valid email')) {
              msg = `Format email tidak valid.`;
            }
            
            const field = d.loc?.[1];
            if (field === 'nik_or_nip') return `NIK: ${msg}`;
            if (field === 'password') return `Kata Sandi: ${msg}`;
            if (field === 'email') return `Email: ${msg}`;
            return msg;
          }).join(' | ');
        }
        throw new Error(errorMsg);
      }

      // Auto login after register
      setAuthMode('login');
      alert('Registrasi berhasil! Silakan login.');
    } catch (e) {
      setAuthError(e.message);
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    setToken('');
    setUserRole('');
    setUserEmail('');
    setMainView('options');
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
        lat: lat ? parseFloat(lat) : null,
        long: long ? parseFloat(long) : null
      };

      const res = await fetch('/api/v1/reports/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Gagal mengirim laporan');
      }

      const data = await res.json();
      setSubmitSuccess(data);
      setJudul('');
      setIsiLaporan('');
      setLat('');
      setLong('');
      fetchReports();
    } catch (e) {
      alert(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  // Status Update Handler
  const handleUpdateStatus = async (reportId) => {
    try {
      const res = await fetch(`/api/v1/reports/${reportId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Gagal memperbarui status');
      }

      fetchReports();
      setSelectedReport(null);
      alert('Status laporan berhasil diperbarui!');
    } catch (e) {
      alert(e.message);
    }
  };

  // Fetch Audit Logs
  const handleViewAuditLogs = async (report) => {
    setSelectedReport(report);
    setShowAuditModal(true);
    try {
      const res = await fetch(`/api/v1/admin/audit-logs/${report.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
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
    setAdminSuccess('');
    try {
      const res = await fetch('/api/v1/admin/admin-dinas', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          nip: adminNip,
          email: adminEmail,
          password: adminPassword
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Gagal membuat akun admin');
      }

      setAdminSuccess(`Akun Admin Dinas (${adminEmail}) berhasil dibuat!`);
      setAdminNip('');
      setAdminEmail('');
      setAdminPassword('');
    } catch (e) {
      alert(e.message);
    }
  };

  // AI Chatbot Handler
  const handleSendChat = async (e) => {
    e.preventDefault();
    if (!chatPrompt.trim()) return;

    const userMsg = chatPrompt;
    setChatMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setChatPrompt('');
    setChatLoading(true);

    try {
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch('/api/v1/chat/', {
        method: 'POST',
        headers,
        body: JSON.stringify({ prompt: userMsg })
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, { role: 'ai', text: data.response }]);
      } else {
        setChatMessages(prev => [...prev, { role: 'ai', text: 'Maaf, terjadi kesalahan saat menghubungi server AI.' }]);
      }
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'ai', text: 'Koneksi terganggu. Silakan coba beberapa saat lagi.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="auth-page-overlay">
        <div className="auth-card">
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <Sparkles className="w-12 h-12 text-accent-primary" style={{ margin: '0 auto' }} />
            <h1 className="auth-title" style={{ marginTop: '1rem' }}>
              {authMode === 'login' ? 'Masuk' : 'Daftar'}
            </h1>
            <p className="auth-subtitle">
              {authMode === 'login' ? 'GOVSMART | PORTAL' : 'WARGA | BARU'}
            </p>
          </div>

          {authError && <p style={{ color: '#e11d48', background: '#fff1f2', padding: '1rem', borderRadius: '8px', fontSize: '0.95rem', marginBottom: '1.5rem', fontWeight: 600 }}>{authError}</p>}

          <form onSubmit={authMode === 'login' ? handleLogin : handleRegister}>
            {authMode === 'register' && (
              <input 
                type="text" 
                className="auth-input" 
                placeholder="NIK KTP (16 DIGIT)" 
                value={regNik} 
                onChange={(e)=>setRegNik(e.target.value)} 
                required 
              />
            )}
            
            <input 
              type="email" 
              className="auth-input" 
              placeholder="ALAMAT EMAIL" 
              value={loginEmail} 
              onChange={(e)=>setLoginEmail(e.target.value)} 
              required 
            />
            
            <input 
              type="password" 
              className="auth-input" 
              placeholder="KATA SANDI" 
              value={loginPassword} 
              onChange={(e)=>setLoginPassword(e.target.value)} 
              required 
            />

            <button type="submit" className="auth-btn">
              {authMode === 'login' ? 'Masuk' : 'Daftar Sekarang'}
            </button>
          </form>

          <div style={{ marginTop: '2.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
            <div style={{ height: '2px', background: '#e2e8f0', flex: 1 }}></div>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Atau akses dengan</span>
            <div style={{ height: '2px', background: '#e2e8f0', flex: 1 }}></div>
          </div>

          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            {authMode === 'login' ? (
              <button className="auth-switch-link" onClick={() => setAuthMode('register')}>Buat akun baru</button>
            ) : (
              <button className="auth-switch-link" onClick={() => setAuthMode('login')}>Sudah punya akun?</button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (mainView === 'options') {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
        <header className="navbar-solid">
          <div className="brand-logo">
            <Sparkles className="w-6 h-6 text-accent-primary" />
            <span>GovSmart AI</span>
          </div>
          <div>
            <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
              {userEmail} ({userRole}) &nbsp;&bull;&nbsp; 
              <button onClick={handleLogout} style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', fontWeight: 700, cursor: 'pointer', fontSize: '1rem' }}>Keluar</button>
            </span>
          </div>
        </header>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem', animation: 'fade-in-up 0.5s ease-out' }}>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '3rem', textAlign: 'center', color: 'var(--text-main)' }}>Pilih Layanan Anda</h1>
          <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            <div onClick={() => setMainView('pengaduan')} className="glass-panel option-card">
              <AlertTriangle size={80} className="text-accent-primary" />
              <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Pengaduan</h2>
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Laporkan masalah infrastruktur atau layanan publik di sekitar Anda.</p>
            </div>
            
            <div onClick={() => setMainView('pertanyaan')} className="glass-panel option-card">
              <MessageSquare size={80} className="text-accent-primary" />
              <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Pertanyaan</h2>
              <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Tanya AI Chatbot mengenai panduan layanan atau perizinan.</p>
            </div>

            {(userRole === 'admin' || userRole === 'super_admin') && (
              <div onClick={() => setMainView('admin')} className="glass-panel option-card">
                <ShieldCheck size={80} className="text-accent-primary" />
                <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Dasbor Admin</h2>
                <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>Manajemen pengaduan masuk dan pembaruan status laporan.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: 'var(--bg-primary)' }}>
      <header className="navbar-solid">
        <div className="brand-logo" onClick={() => setMainView('options')} style={{ cursor: 'pointer' }}>
          <Sparkles className="w-6 h-6 text-accent-primary" />
          <span>GovSmart AI</span>
        </div>
        <div>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-main)' }}>
            {userEmail} ({userRole}) &nbsp;&bull;&nbsp; 
            <button onClick={handleLogout} style={{ background: 'none', border: 'none', color: 'var(--accent-rose)', fontWeight: 700, cursor: 'pointer', fontSize: '1rem' }}>Keluar</button>
          </span>
        </div>
      </header>

      <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto', width: '100%', animation: 'fade-in-up 0.5s ease-out' }}>
        <button className="nav-btn" onClick={() => setMainView('options')} style={{ marginBottom: '2rem' }}>&larr; Kembali ke Pilihan</button>
        
        {mainView === 'pengaduan' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
            <div id="form-pengaduan" className="glass-panel">
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText className="text-accent-primary" /> Buat Pengaduan Baru
              </h2>

              {submitSuccess && (
                <div style={{ background: '#ecfdf5', border: '1px solid #10b981', padding: '1rem', borderRadius: '12px', marginBottom: '1.5rem' }}>
                  <div style={{ fontWeight: 700, color: '#059669', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckCircle size={18} /> Laporan Diterima & Teranalisis AI!
                  </div>
                  <p style={{ fontSize: '0.9rem', color: 'var(--text-main)' }}>
                    Urgency AI: <span className={`badge badge-${submitSuccess.urgensi}`}>{submitSuccess.urgensi}</span>
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmitReport}>
                <div className="form-group">
                  <label className="form-label">Judul Pengaduan</label>
                  <input type="text" className="form-input" placeholder="Contoh: Jalan berlubang dan ambruk di Babat" value={judul} onChange={(e) => setJudul(e.target.value)} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Isi Detail Laporan</label>
                  <textarea className="form-textarea" rows={5} placeholder="Jelaskan lokasi rinci, kondisi, dan bahaya yang ditimbulkan..." value={isiLaporan} onChange={(e) => setIsiLaporan(e.target.value)} required />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group">
                    <label className="form-label">Latitude (Opsional)</label>
                    <input type="number" step="any" className="form-input" placeholder="-7.1123" value={lat} onChange={(e) => setLat(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Longitude (Opsional)</label>
                    <input type="number" step="any" className="form-input" placeholder="112.1554" value={long} onChange={(e) => setLong(e.target.value)} />
                  </div>
                </div>
                <button type="submit" className="nav-btn nav-btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '1rem', padding: '0.85rem' }} disabled={submitting}>
                  <Send size={18} /> {submitting ? 'Menganalisis AI & Kirim...' : 'Kirim Pengaduan'}
                </button>
              </form>
            </div>

            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Clock className="text-accent-primary" /> Feed Pengaduan Publik
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {reports.map((report) => (
                  <div key={report.id} className="glass-panel" style={{ padding: '1.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                      <span className={`badge badge-${report.urgensi}`}>
                        {report.urgensi === 'darurat' && <AlertTriangle size={12} />}
                        {report.urgensi}
                      </span>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-dim)', fontWeight: 600 }}>
                        Status: <strong style={{ color: 'var(--accent-primary)' }}>{report.status}</strong>
                      </span>
                    </div>
                    <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--text-main)' }}>{report.judul}</h3>
                    <p style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '1.25rem', lineHeight: 1.6 }}>{report.isi_laporan}</p>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-dim)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #e2e8f0', paddingTop: '1rem' }}>
                      <span><Building2 size={14} style={{ display: 'inline', marginRight:'4px' }} /> Dinas ID: {report.dept_id || 'AI Auto-Routing'}</span>
                      <span>{new Date(report.created_at).toLocaleDateString('id-ID')}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {mainView === 'pertanyaan' && (
          <div className="glass-panel" style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
              <Bot size={32} className="text-accent-primary" />
              <h2 style={{ fontSize: '1.75rem', fontWeight: 800 }}>Tanya AI GovSmart</h2>
            </div>
            
            <div style={{ height: '400px', overflowY: 'auto', marginBottom: '2rem', padding: '1rem', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {chatMessages.map((msg, i) => (
                <div key={i} className={`chat-msg ${msg.role === 'user' ? 'chat-msg-user' : 'chat-msg-ai'}`} style={{ maxWidth: '85%', padding: '0.85rem 1.2rem', borderRadius: '12px', fontSize: '1rem', lineHeight: 1.5, alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', background: msg.role === 'user' ? 'var(--accent-primary)' : '#ffffff', color: msg.role === 'user' ? '#ffffff' : '#000000', border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0' }}>
                  {msg.text}
                </div>
              ))}
              {chatLoading && (
                <div className="chat-msg chat-msg-ai typing-indicator" style={{ alignSelf: 'flex-start', background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px' }}>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              )}
            </div>

            <form onSubmit={handleSendChat} style={{ display: 'flex', gap: '1rem' }}>
              <input type="text" className="form-input" placeholder="Tanyakan panduan atau lapor..." value={chatPrompt} onChange={(e) => setChatPrompt(e.target.value)} style={{ flex: 1 }} />
              <button type="submit" className="nav-btn nav-btn-primary" style={{ padding: '0.85rem 1.5rem' }}>
                <Send size={18} /> Kirim
              </button>
            </form>
          </div>
        )}

        {mainView === 'admin' && (userRole === 'admin' || userRole === 'super_admin') && (
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: '2rem' }}>
              Dasbor Manajemen & Penanganan Pengaduan
            </h1>
            {userRole === 'super_admin' && (
              <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2.5rem' }}>
                <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <UserPlus className="text-accent-primary" /> Registrasi Akun Admin Dinas Baru
                </h2>
                {adminSuccess && <p style={{ color: '#059669', background:'#ecfdf5', padding:'1rem', borderRadius:'8px', fontWeight:600, marginBottom: '1.5rem' }}>{adminSuccess}</p>}
                <form onSubmit={handleCreateAdminDinas} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: '1rem', alignItems: 'end' }}>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">NIP Aparatur</label>
                    <input type="text" className="form-input" placeholder="198505052010011005" value={adminNip} onChange={(e)=>setAdminNip(e.target.value)} required />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Email Dinas</label>
                    <input type="email" className="form-input" placeholder="admin.pu@lamongan.go.id" value={adminEmail} onChange={(e)=>setAdminEmail(e.target.value)} required />
                  </div>
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label">Password</label>
                    <input type="password" className="form-input" placeholder="••••••••" value={adminPassword} onChange={(e)=>setAdminPassword(e.target.value)} required />
                  </div>
                  <button type="submit" className="nav-btn nav-btn-primary" style={{ padding: '0.85rem 1.5rem' }}>Buat Akun</button>
                </form>
              </div>
            )}
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.5rem' }}>Daftar Pengaduan Masuk</h2>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--border-color)', textAlign: 'left', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '1rem' }}>ID</th>
                    <th style={{ padding: '1rem' }}>Urgensi AI</th>
                    <th style={{ padding: '1rem' }}>Judul Laporan</th>
                    <th style={{ padding: '1rem' }}>Status</th>
                    <th style={{ padding: '1rem' }}>Aksi</th>
                  </tr>
                </thead>
                <tbody>
                  {reports.map((r) => (
                    <tr key={r.id} style={{ borderBottom: '1px solid #e2e8f0' }}>
                      <td style={{ padding: '1rem', fontWeight: 600 }}>#{r.id}</td>
                      <td style={{ padding: '1rem' }}><span className={`badge badge-${r.urgensi}`}>{r.urgensi}</span></td>
                      <td style={{ padding: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>{r.judul}</td>
                      <td style={{ padding: '1rem' }}><span style={{ color: r.status === 'selesai' ? '#059669' : '#b45309', fontWeight: 700 }}>{r.status}</span></td>
                      <td style={{ padding: '1rem', display: 'flex', gap: '0.5rem' }}>
                        <button className="nav-btn" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }} onClick={() => { setSelectedReport(r); setNewStatus(r.status); }}>Ubah Status</button>
                        <button className="nav-btn" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem', borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }} onClick={() => handleViewAuditLogs(r)}>Audit Log</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Modals for Admin Actions */}
      {selectedReport && !showAuditModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '1rem' }}>Pembaruan Status Laporan #{selectedReport.id}</h3>
            <p style={{ fontSize: '1rem', color: 'var(--text-muted)', marginBottom: '1.5rem', lineHeight: 1.5 }}>{selectedReport.judul}</p>
            <div className="form-group">
              <label className="form-label">Pilih Status Baru</label>
              <select className="form-select" value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                <option value="menunggu">Menunggu</option>
                <option value="diproses">Diproses</option>
                <option value="selesai">Selesai</option>
                <option value="ditolak">Ditolak</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '2rem' }}>
              <button className="nav-btn" onClick={() => setSelectedReport(null)}>Batal</button>
              <button className="nav-btn nav-btn-primary" onClick={() => handleUpdateStatus(selectedReport.id)}>Simpan Perubahan</button>
            </div>
          </div>
        </div>
      )}

      {showAuditModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800 }}>Riwayat Status (Log #{selectedReport?.id})</h3>
              <button className="nav-btn" onClick={() => setShowAuditModal(false)}><X size={20} /></button>
            </div>
            <div style={{ maxHeight: '350px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {auditLogs.map((log) => (
                <div key={log.id} style={{ background: '#f8fafc', padding: '1rem', borderRadius: '12px', borderLeft: '4px solid var(--accent-primary)' }}>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Oleh User ID #{log.admin_id} &bull; {new Date(log.created_at).toLocaleString('id-ID')}</div>
                  <div style={{ fontSize: '1.05rem', marginTop: '0.5rem', color: 'var(--text-main)' }}>
                    Status: <span style={{ textDecoration: 'line-through', color: 'var(--text-dim)' }}>{log.status_lama || 'baru'}</span> &rarr; <strong style={{ color: 'var(--accent-primary)' }}>{log.status_baru}</strong>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
