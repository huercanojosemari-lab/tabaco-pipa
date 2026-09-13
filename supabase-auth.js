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

function metadataFromForm() {
  return {
    display_name: $('name')?.value.trim() || '',
    country: $('country')?.value.trim() || '',
    age_confirmed: true
  };
}

function pageUrl(name) {
  return new URL(name, window.location.href).href;
}

async function refreshSession() {
  if (!supabase) return;
  const { data: { session } } = await supabase.auth.getSession();
  const logged = Boolean(session);
  $('loggedOut')?.toggleAttribute('hidden', logged);
  $('loggedIn')?.toggleAttribute('hidden', !logged);
  if (session?.user) {
    $('accountEmail')?.replaceChildren(document.createTextNode(session.user.email || ''));
    $('accountName')?.replaceChildren(document.createTextNode(session.user.user_metadata?.display_name || 'Lector de Pipateka'));
  }
}

if (!configured) {
  status('La interfaz de cuenta está lista. Falta configurar la URL y la Publishable Key de tu proyecto Supabase en supabase-config.js.', 'warning');
}

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
      emailRedirectTo: pageUrl('registro.html')
    }
  });
  if (error) return status(error.message, 'error');
  if (data.session) {
    status('Cuenta creada y sesión iniciada.', 'success');
    await refreshSession();
  } else {
    status('Cuenta creada. Revisa tu correo para confirmar la dirección antes de iniciar sesión.', 'success');
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
    redirectTo: pageUrl('cambiar-contrasena.html')
  });
  if (error) return status(error.message, 'error');
  status('Si el correo existe, recibirás un enlace para cambiar la contraseña.', 'success');
});

$('changePasswordForm')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!supabase) return status('Configura primero Supabase en supabase-config.js.', 'warning');
  const password = $('newPassword').value;
  const confirmation = $('confirmPassword').value;
  if (password.length < 8) return status('La contraseña debe tener al menos 8 caracteres.', 'warning');
  if (password !== confirmation) return status('Las contraseñas no coinciden.', 'warning');
  status('Guardando nueva contraseña…');
  const { error } = await supabase.auth.updateUser({ password });
  if (error) return status(error.message, 'error');
  status('Contraseña actualizada correctamente. Ya puedes iniciar sesión.', 'success');
  event.currentTarget.reset();
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
