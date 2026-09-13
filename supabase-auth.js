import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

const cfg = window.PIPATEKA_SUPABASE || {};
const configured = Boolean(cfg.url && cfg.publishableKey && !cfg.url.includes('TU-PROYECTO') && !cfg.publishableKey.includes('TU_CLAVE'));
const supabase = configured ? createClient(cfg.url, cfg.publishableKey, {
  auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
}) : null;

const $ = (id) => document.getElementById(id);
const status = (message, kind = 'info') => {
  const el = $('authStatus');
  if (!el) return;
  el.textContent = message;
  el.dataset.kind = kind;
  el.hidden = false;
};

function setMode(mode) {
  document.querySelectorAll('[data-auth-mode]').forEach((button) => {
    button.classList.toggle('active', button.dataset.authMode === mode);
  });
  document.querySelectorAll('.auth-panel').forEach((panel) => {
    panel.hidden = panel.dataset.panel !== mode;
  });
}

function metadataFromForm() {
  return {
    display_name: $('name')?.value.trim() || '',
    country: $('country')?.value.trim() || '',
    age_confirmed: true
  };
}

async function refreshSession() {
  if (!supabase) return;
  const { data: { session } } = await supabase.auth.getSession();
  const logged = Boolean(session);
  $('loggedOut')?.toggleAttribute('hidden', logged);
  $('loggedIn')?.toggleAttribute('hidden', !logged);
  if (session?.user) {
    $('accountEmail').textContent = session.user.email || '';
    $('accountName').textContent = session.user.user_metadata?.display_name || 'Lector de Pipateka';
  }
}

if (!configured) {
  status('La interfaz de cuenta está lista. Falta configurar la URL y la Publishable Key de tu proyecto Supabase en supabase-config.js.', 'warning');
}

document.querySelectorAll('[data-auth-mode]').forEach((button) => {
  button.addEventListener('click', () => setMode(button.dataset.authMode));
});

$('registerAuthForm')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!supabase) return status('Configura primero Supabase en supabase-config.js.', 'warning');
  if (!$('age_confirmed').checked || !$('privacy_consent').checked) return status('Debes confirmar que tienes 18 años o más y aceptar la información de privacidad.', 'warning');
  const email = $('registerEmail').value.trim();
  const password = $('registerPassword').value;
  if (password.length < 8) return status('La contraseña debe tener al menos 8 caracteres.', 'warning');
  status('Creando tu cuenta…');
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadataFromForm(),
      emailRedirectTo: `${location.origin}${location.pathname}`
    }
  });
  if (error) return status(error.message, 'error');
  if (data.session) {
    status('Cuenta creada y sesión iniciada.', 'success');
    await refreshSession();
  } else {
    status('Cuenta creada. Revisa tu correo para confirmar la dirección antes de iniciar sesión.', 'success');
    setMode('login');
  }
});

$('loginAuthForm')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!supabase) return status('Configura primero Supabase en supabase-config.js.', 'warning');
  status('Iniciando sesión…');
  const { error } = await supabase.auth.signInWithPassword({
    email: $('loginEmail').value.trim(),
    password: $('loginPassword').value
  });
  if (error) return status(error.message, 'error');
  status('Sesión iniciada correctamente.', 'success');
  await refreshSession();
});

$('resetAuthForm')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!supabase) return status('Configura primero Supabase en supabase-config.js.', 'warning');
  status('Enviando enlace de recuperación…');
  const { error } = await supabase.auth.resetPasswordForEmail($('resetEmail').value.trim(), {
    redirectTo: `${location.origin}${location.pathname}?mode=reset`
  });
  if (error) return status(error.message, 'error');
  status('Si el correo existe, recibirás un enlace para restablecer la contraseña.', 'success');
});

$('logoutButton')?.addEventListener('click', async () => {
  if (!supabase) return;
  const { error } = await supabase.auth.signOut();
  if (error) return status(error.message, 'error');
  status('Sesión cerrada.', 'success');
  await refreshSession();
});

if (supabase) {
  supabase.auth.onAuthStateChange(() => refreshSession());
  refreshSession();
}

const requestedMode = new URLSearchParams(location.search).get('mode');
setMode(requestedMode === 'reset' ? 'reset' : 'register');
