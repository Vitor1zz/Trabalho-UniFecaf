const SITE_URL = "http://127.0.0.1:5000";
const API_ORIGIN =
    window.location.protocol === "file:" ? SITE_URL : window.location.origin;
const API_BASE_URL = `${API_ORIGIN}/api`;

let apiOnline = false;
const TOKEN_KEY = "smartFoodToken";
const SESSION_KEY = "smartFoodSession";
const USER_KEY = "smartFoodUser";
const REGISTERED_USERS_KEY = "smartFoodRegisteredUsers";
const TOKEN_TTL_MS = 1000 * 60 * 60 * 24 * 7;
const WINDOW_TRANSITION_MS = 700;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const KNOWN_USERS = ["usuario@email.com", "gustavo@email.com", "demo@smartfood.com"];

const fallbackRestaurants = [
    {
        name: "Natural Garden",
        rating: 4.9,
        nutritionSeal: true,
        cuisine: "saudavel",
        items: [
            {
                dish: "Bowl de Salmao",
                protein: 35,
                calories: 520,
                iFoodPrice: 42,
                food99Price: 38,
                iFoodDelivery: 32,
                food99Delivery: 29,
                link: "#"
            },
            {
                dish: "Salada Proteica",
                protein: 28,
                calories: 390,
                iFoodPrice: 34,
                food99Price: 35,
                iFoodDelivery: 28,
                food99Delivery: 26,
                link: "#"
            }
        ]
    },
    {
        name: "Poke Mania",
        rating: 4.7,
        nutritionSeal: true,
        cuisine: "japonesa",
        items: [
            {
                dish: "Poke Tuna Fit",
                protein: 32,
                calories: 470,
                iFoodPrice: 39,
                food99Price: 37,
                iFoodDelivery: 35,
                food99Delivery: 31,
                link: "#"
            },
            {
                dish: "Bowl de Frango Grelhado",
                protein: 30,
                calories: 440,
                iFoodPrice: 36,
                food99Price: 34,
                iFoodDelivery: 34,
                food99Delivery: 33,
                link: "#"
            }
        ]
    },
    {
        name: "Burger King",
        rating: 4.5,
        nutritionSeal: false,
        cuisine: "fast food",
        items: [
            {
                dish: "Whopper",
                protein: 25,
                calories: 670,
                iFoodPrice: 31,
                food99Price: 33,
                iFoodDelivery: 22,
                food99Delivery: 25,
                link: "#"
            },
            {
                dish: "Chicken Duplo",
                protein: 29,
                calories: 740,
                iFoodPrice: 35,
                food99Price: 34,
                iFoodDelivery: 24,
                food99Delivery: 26,
                link: "#"
            }
        ]
    }
];

let restaurants = [...fallbackRestaurants];

const viewLogin = document.getElementById("view-login");
const viewRegister = document.getElementById("view-register");
const viewApp = document.getElementById("view-app");
const viewOffline = document.getElementById("view-offline");
const userGreeting = document.getElementById("user-greeting");
const tabButtons = document.querySelectorAll(".tab");
const panelCompare = document.getElementById("panel-compare");
const panelAssistant = document.getElementById("panel-assistant");
const compareSearchForm = document.getElementById("compare-search-form");
const compareQueryInput = document.getElementById("compare-query");
const sortBySelect = document.getElementById("sort-by");
const cuisineFilterSelect = document.getElementById("cuisine-filter");
let searchTerm = "";
const loginForm = document.getElementById("login-form");
const loginEmail = document.getElementById("login-email");
const loginPassword = document.getElementById("login-password");
const rememberMe = document.getElementById("remember-me");
const loginMessage = document.getElementById("login-message");
const togglePasswordBtn = document.getElementById("toggle-password");
const goRegisterBtn = document.getElementById("go-register");
const backLoginBtn = document.getElementById("back-login");
const registerForm = document.getElementById("register-form");
const registerName = document.getElementById("register-name");
const registerEmail = document.getElementById("register-email");
const registerPassword = document.getElementById("register-password");
const registerConfirm = document.getElementById("register-confirm");
const registerMessage = document.getElementById("register-message");
const logoutBtn = document.getElementById("logout-btn");

const restaurantList = document.getElementById("restaurant-list");
const aiForm = document.getElementById("ai-form");
const aiResponse = document.getElementById("ai-response");
const knownUsersSet = new Set(KNOWN_USERS.map((email) => email.toLowerCase()));
const serverBanner = document.getElementById("server-banner");
const loginSubmitBtn = document.getElementById("login-submit");
const registerSubmitBtn = document.getElementById("register-submit");

function setAuthFormsEnabled(enabled) {
    if (loginSubmitBtn) {
        loginSubmitBtn.disabled = !enabled;
    }
    if (registerSubmitBtn) {
        registerSubmitBtn.disabled = !enabled;
    }
}

function hideServerBanner() {
    if (serverBanner) {
        serverBanner.classList.add("hidden");
        serverBanner.setAttribute("aria-hidden", "true");
    }
}

async function checkApiOnline() {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 4000);
    try {
        const response = await fetch(`${API_BASE_URL}/ping`, {
            signal: controller.signal,
            cache: "no-store"
        });
        return response.ok;
    } catch (_error) {
        return false;
    } finally {
        clearTimeout(timeout);
    }
}

async function refreshServerStatus() {
    hideServerBanner();

    if (window.location.protocol === "file:") {
        apiOnline = await checkApiOnline();
        if (apiOnline) {
            window.location.replace(SITE_URL);
            return true;
        }
        showOfflineView();
        return false;
    }

    if (window.location.origin !== SITE_URL) {
        apiOnline = await checkApiOnline();
        if (apiOnline) {
            window.location.replace(SITE_URL);
            return true;
        }
        showOfflineView();
        return false;
    }

    apiOnline = await checkApiOnline();
    if (!apiOnline) {
        showOfflineView();
        return false;
    }

    setAuthFormsEnabled(true);
    return true;
}

function showOfflineView() {
    setActiveView("offline");
    setAuthFormsEnabled(false);
}

function showLogin() {
    if (!apiOnline) {
        showOfflineView();
        return;
    }
    setActiveView("login");
}

function setLoginMessage(message, isError = true) {
    loginMessage.textContent = message;
    loginMessage.classList.toggle("ok", !isError && Boolean(message));
}

function setRegisterMessage(message, isError = true) {
    registerMessage.textContent = message;
    registerMessage.classList.toggle("ok", !isError && Boolean(message));
}

function setActiveView(viewName) {
    const views = { login: viewLogin, register: viewRegister, app: viewApp, offline: viewOffline };
    Object.values(views).forEach((el) => el.classList.remove("view-active"));
    const target = views[viewName];
    if (target) {
        target.classList.add("view-active");
    }
    document.body.dataset.view = viewName;
}

function switchAppTab(tabName) {
    tabButtons.forEach((btn) => {
        const active = btn.dataset.tab === tabName;
        btn.classList.toggle("tab-active", active);
        btn.setAttribute("aria-selected", active ? "true" : "false");
    });

    const panels = {
        compare: panelCompare,
        assistant: panelAssistant
    };
    Object.entries(panels).forEach(([name, panel]) => {
        if (!panel) {
            return;
        }
        const active = name === tabName;
        panel.classList.toggle("panel-active", active);
        panel.hidden = !active;
    });
}

function getItemPrices(item) {
    const ifood = Number(item.iFoodPrice) || 0;
    const food99 = Number(item.food99Price) || 0;
    return { ifood, food99 };
}

function getPlatformMinPrices(restaurant) {
    const items = restaurant.items || [];
    let ifoodMin = Number.POSITIVE_INFINITY;
    let food99Min = Number.POSITIVE_INFINITY;

    items.forEach((item) => {
        const { ifood, food99 } = getItemPrices(item);
        if (ifood > 0 && ifood < ifoodMin) {
            ifoodMin = ifood;
        }
        if (food99 > 0 && food99 < food99Min) {
            food99Min = food99;
        }
    });

    return {
        ifood: ifoodMin === Number.POSITIVE_INFINITY ? 0 : ifoodMin,
        food99: food99Min === Number.POSITIVE_INFINITY ? 0 : food99Min
    };
}

function getBestDeal(restaurant) {
    const { ifood, food99 } = getPlatformMinPrices(restaurant);

    if (ifood <= 0 && food99 <= 0) {
        return { platform: null, price: 0, savings: 0 };
    }
    if (ifood <= 0) {
        return { platform: "99", price: food99, savings: 0 };
    }
    if (food99 <= 0) {
        return { platform: "ifood", price: ifood, savings: 0 };
    }
    if (food99 < ifood) {
        return { platform: "99", price: food99, savings: ifood - food99 };
    }
    if (ifood < food99) {
        return { platform: "ifood", price: ifood, savings: food99 - ifood };
    }
    return { platform: "empate", price: ifood, savings: 0 };
}

function getCheapestPrice(restaurant) {
    const best = getBestDeal(restaurant);
    return {
        price: best.price || Number.POSITIVE_INFINITY,
        platform: best.platform
    };
}

function formatPlatformPrice(value) {
    return value > 0 ? `R$ ${formatPrice(value)}` : "—";
}

function getIfoodRating(restaurant) {
    const ifood = restaurant.ifood || {};
    const food99 = restaurant.food99 || {};
    return Math.max(
        Number(ifood.rating || 0),
        Number(food99.rating || 0),
        Number(restaurant.rating) || 0
    );
}

function getDeliveryMinutes(restaurant) {
    return Number(restaurant.ifood?.deliveryTime) || 30;
}

function restaurantMatchesSearch(restaurant) {
    if (!searchTerm) {
        return true;
    }
    const q = searchTerm.toLowerCase();
    const haystack = [
        restaurant.name,
        restaurant.cuisine,
        ...(restaurant.items || []).map((i) => i.dish)
    ]
        .join(" ")
        .toLowerCase();
    return haystack.includes(q);
}

function getFilteredSortedRestaurants() {
    const cuisine = (cuisineFilterSelect?.value || "").toLowerCase();
    const sortBy = sortBySelect?.value || "price";

    let list = restaurants.filter((r) => {
        if (cuisine && !(r.cuisine || "").toLowerCase().includes(cuisine)) {
            return false;
        }
        return restaurantMatchesSearch(r);
    });

    list = [...list].sort((a, b) => {
        if (sortBy === "rating") {
            return getIfoodRating(b) - getIfoodRating(a);
        }
        return getCheapestPrice(a).price - getCheapestPrice(b).price;
    });

    return list;
}

function populateCuisineFilter() {
    if (!cuisineFilterSelect) {
        return;
    }
    const cuisines = new Set(
        restaurants.map((r) => (r.cuisine || "").trim()).filter(Boolean)
    );
    const current = cuisineFilterSelect.value;
    cuisineFilterSelect.innerHTML =
        '<option value="">Todas cozinhas</option>' +
        [...cuisines]
            .sort((a, b) => a.localeCompare(b, "pt-BR"))
            .map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`)
            .join("");
    if (current && cuisines.has(current)) {
        cuisineFilterSelect.value = current;
    }
}

async function loadIfoodStatus() {
    const statusEl = document.getElementById("ifood-status");
    try {
        const response = await fetch(`${API_BASE_URL}/ifood/status`);
        if (!response.ok) {
            return;
        }
        const data = await response.json();
        if (statusEl) {
            statusEl.classList.add("hidden");
            if (!data.conectado) {
                statusEl.textContent = "Modo demo";
                statusEl.classList.remove("hidden");
            }
        }
    } catch (_error) {
        if (statusEl) {
            statusEl.textContent = "Offline";
            statusEl.classList.remove("hidden");
        }
    }
}

function updateGreeting(email, name = "") {
    if (!userGreeting) {
        return;
    }
    userGreeting.textContent = name ? `Ola, ${name}` : email;
}

function loadRegisteredUsers() {
    const stored = localStorage.getItem(REGISTERED_USERS_KEY);
    if (!stored) {
        return;
    }
    try {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed)) {
            parsed.forEach((email) => {
                if (typeof email === "string") {
                    knownUsersSet.add(email.toLowerCase());
                }
            });
        }
    } catch (_error) {
        localStorage.removeItem(REGISTERED_USERS_KEY);
    }
}

function saveRegisteredUser(email) {
    const normalized = email.toLowerCase();
    knownUsersSet.add(normalized);
    localStorage.setItem(REGISTERED_USERS_KEY, JSON.stringify(Array.from(knownUsersSet)));
}

function generateToken(email) {
    const raw = `${email}:${Date.now()}:${Math.random().toString(36).slice(2)}`;
    return btoa(raw);
}

function persistAuth(token, email, keepConnected, name = "") {
    const expiresAt = Date.now() + TOKEN_TTL_MS;
    const payload = JSON.stringify({ token, expiresAt });
    const userPayload = JSON.stringify({ email, name });

    if (keepConnected) {
        localStorage.setItem(TOKEN_KEY, payload);
        localStorage.removeItem(SESSION_KEY);
    } else {
        sessionStorage.setItem(SESSION_KEY, payload);
        localStorage.removeItem(TOKEN_KEY);
    }

    localStorage.setItem(USER_KEY, userPayload);
}

function readStoredAuth() {
    const authRaw = localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(SESSION_KEY);
    const userRaw = localStorage.getItem(USER_KEY);

    if (!authRaw || !userRaw) {
        return null;
    }

    try {
        const auth = JSON.parse(authRaw);
        const user = JSON.parse(userRaw);
        if (!auth.token || !auth.expiresAt || !user.email) {
            return null;
        }
        if (Date.now() > auth.expiresAt) {
            clearAuth();
            return null;
        }
        return { token: auth.token, email: user.email, name: user.name || "" };
    } catch (_error) {
        clearAuth();
        return null;
    }
}

function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    sessionStorage.removeItem(SESSION_KEY);
}

function showApp(email = "", name = "") {
    setActiveView("app");
    switchAppTab("compare");
    if (email) {
        updateGreeting(email, name);
    }
}

function showRegister() {
    if (!apiOnline) {
        showOfflineView();
        return;
    }
    setActiveView("register");
}

function openWindow(name, user = {}) {
    if (name === "login") {
        showLogin();
        return;
    }
    if (name === "register") {
        showRegister();
        return;
    }
    showApp(user.email || "", user.name || "");
}

function goToRegisterScreen() {
    setLoginMessage("");
    loginForm.reset();
    setRegisterMessage("");
    openWindow("register");
}

function goToLoginScreen(options = {}) {
    const { message = "", isError = false, prefillEmail = "" } = options;
    setRegisterMessage("");
    registerForm.reset();
    openWindow("login");
    if (prefillEmail) {
        loginEmail.value = prefillEmail;
    }
    setLoginMessage(message, isError);
}

async function checkEmailExists(email) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/exists?email=${encodeURIComponent(email)}`);
        if (response.ok) {
            const data = await response.json();
            return Boolean(data.exists);
        }
    } catch (_error) {
        return null;
    }
    return null;
}

async function loginWithApi(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, senha: password })
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok && data.token) {
            return {
                ok: true,
                token: data.token,
                email: data.email || email,
                name: data.name || ""
            };
        }
        return {
            ok: false,
            message: data.error || "E-mail ou senha incorretos."
        };
    } catch (_error) {
        return {
            ok: false,
            message: "Servidor offline. Execute iniciar.bat e use http://127.0.0.1:5000"
        };
    }
}

function formatPrice(value) {
    return Number(value).toFixed(2).replace(".", ",");
}

function renderRestaurants() {
    if (!restaurantList) {
        return;
    }

    populateCuisineFilter();
    const filtered = getFilteredSortedRestaurants();

    if (!filtered.length) {
        restaurantList.innerHTML = `<p class="compare-empty">Nenhum resultado.</p>`;
        return;
    }

    restaurantList.innerHTML = filtered
        .map((restaurant) => {
            const ifood = restaurant.ifood || {};
            const food99 = restaurant.food99 || {};
            const prices = getPlatformMinPrices(restaurant);
            const best = getBestDeal(restaurant);
            const rating = getIfoodRating(restaurant).toFixed(1);
            const cuisine = escapeHtml(restaurant.cuisine || "");
            const ifoodUrl = ifood.url || "https://www.ifood.com.br";
            const food99Url = food99.url || "https://food.99app.com";

            const ifoodBest = best.platform === "ifood" || best.platform === "empate";
            const food99Best = best.platform === "99" || best.platform === "empate";

            let bestLine = "";
            if (best.platform === "ifood") {
                bestLine = `Melhor preco: iFood · economize R$ ${formatPrice(best.savings)}`;
            } else if (best.platform === "99") {
                bestLine = `Melhor preco: 99 Food · economize R$ ${formatPrice(best.savings)}`;
            } else if (best.platform === "empate") {
                bestLine = "Mesmo preco nos dois apps";
            }

            return `
                <article class="compare-card">
                    <div class="compare-header">
                        <h3 class="compare-name">${escapeHtml(restaurant.name)}</h3>
                        <p class="compare-meta">${cuisine}${cuisine ? " · " : ""}${rating}</p>
                    </div>
                    <div class="platform-compare">
                        <div class="platform-offer platform-offer--ifood${ifoodBest ? " is-best" : ""}">
                            <span class="platform-label">iFood</span>
                            <span class="platform-price">${formatPlatformPrice(prices.ifood)}</span>
                            ${ifoodBest && best.platform !== "empate" ? '<span class="best-tag">Melhor</span>' : ""}
                            <a class="btn btn-ifood btn-sm btn-block" href="${ifoodUrl}" target="_blank" rel="noopener noreferrer">Pedir</a>
                        </div>
                        <div class="platform-offer platform-offer--99${food99Best ? " is-best" : ""}">
                            <span class="platform-label">99 Food</span>
                            <span class="platform-price">${formatPlatformPrice(prices.food99)}</span>
                            ${food99Best && best.platform !== "empate" ? '<span class="best-tag">Melhor</span>' : ""}
                            <a class="btn btn-food99 btn-sm btn-block" href="${food99Url}" target="_blank" rel="noopener noreferrer">Pedir</a>
                        </div>
                    </div>
                    ${bestLine ? `<p class="compare-best">${bestLine}</p>` : ""}
                </article>
            `;
        })
        .join("");
}

async function syncDeliveryPrices() {
    const statusEl = document.getElementById("ifood-status");
    const term = compareQueryInput?.value.trim() || searchTerm || "";
    const searchBtn = document.getElementById("compare-search-btn");
    const body = JSON.stringify({ term });

    if (searchBtn) {
        searchBtn.disabled = true;
        searchBtn.textContent = "...";
    }

    try {
        await Promise.all([
            fetch(`${API_BASE_URL}/ifood/atualizar`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body
            }),
            fetch(`${API_BASE_URL}/food99/atualizar`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body
            })
        ]);
        await loadRestaurants(false);
        if (statusEl) {
            statusEl.classList.add("hidden");
        }
    } catch (_error) {
        if (statusEl) {
            statusEl.textContent = "Erro na busca";
            statusEl.classList.remove("hidden");
        }
    } finally {
        if (searchBtn) {
            searchBtn.disabled = false;
            searchBtn.textContent = "Buscar";
        }
    }
}

async function loadRestaurants(runSync = true) {
    await loadIfoodStatus();

    if (runSync) {
        try {
            const body = JSON.stringify({ term: searchTerm });
            await Promise.all([
                fetch(`${API_BASE_URL}/ifood/atualizar`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body
                }),
                fetch(`${API_BASE_URL}/food99/atualizar`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body
                })
            ]);
        } catch (_error) {
            /* cache local */
        }
    }

    try {
        const response = await fetch(`${API_BASE_URL}/restaurants`);
        if (!response.ok) {
            throw new Error("Falha ao buscar restaurantes da API.");
        }
        const data = await response.json();
        const list = Array.isArray(data) ? data : data.restaurants;
        if (Array.isArray(list) && list.length) {
            restaurants = list;
        }
        await loadIfoodStatus();
    } catch (_error) {
        restaurants = [...fallbackRestaurants];
    } finally {
        renderRestaurants();
    }
}

function localRecommendation(payload) {
    const preferenceText = payload.preferences.toLowerCase();
    const options = [];

    restaurants.forEach((restaurant) => {
        restaurant.items.forEach((item) => {
            const selectedPlatform =
                payload.platform === "iFood"
                    ? { name: "iFood", price: item.iFoodPrice, delivery: item.iFoodDelivery }
                    : payload.platform === "99 Food"
                      ? { name: "99 Food", price: item.food99Price, delivery: item.food99Delivery }
                      : item.iFoodPrice <= item.food99Price
                        ? { name: "iFood", price: item.iFoodPrice, delivery: item.iFoodDelivery }
                        : { name: "99 Food", price: item.food99Price, delivery: item.food99Delivery };

            if (selectedPlatform.price <= payload.budget) {
                options.push({ restaurant, item, platform: selectedPlatform });
            }
        });
    });

    const byPreference = options.filter(
        (option) =>
            option.restaurant.cuisine.includes(preferenceText) ||
            option.item.dish.toLowerCase().includes(preferenceText)
    );

    return (byPreference.length ? byPreference : options)[0] || null;
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function formatAiMessage(text) {
    return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function renderRecommendation(data) {
    switchAppTab("assistant");
    aiResponse.classList.remove("ai-box--empty");
    const is99 = data.platform === "99 Food";
    const btnClass = is99 ? "btn-food99" : "btn-ifood";
    const label = is99 ? "Pedir na 99" : "Pedir no iFood";
    const fallback = is99 ? "https://food.99app.com" : "https://www.ifood.com.br";
    aiResponse.innerHTML = `
        <h3>${escapeHtml(data.dish)}</h3>
        <p class="compare-meta">${escapeHtml(data.restaurant)}</p>
        <p class="compare-best">Melhor preco: ${escapeHtml(data.platform)} · R$ ${formatPrice(data.price)}</p>
        <a class="btn ${btnClass} btn-sm" href="${data.link || fallback}" target="_blank" rel="noopener noreferrer">${label}</a>
    `;
}

if (togglePasswordBtn) {
    togglePasswordBtn.addEventListener("click", () => {
        const isPassword = loginPassword.type === "password";
        loginPassword.type = isPassword ? "text" : "password";
        togglePasswordBtn.textContent = isPassword ? "◌" : "●";
    });
}

tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => switchAppTab(btn.dataset.tab));
});

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setLoginMessage("");

    if (!apiOnline && !(await refreshServerStatus())) {
        setLoginMessage("Servidor offline. Execute iniciar.bat e acesse http://127.0.0.1:5000");
        return;
    }

    const email = loginEmail.value.trim().toLowerCase();
    const password = loginPassword.value.trim();
    const keepConnected = rememberMe.checked;

    if (!EMAIL_REGEX.test(email)) {
        setLoginMessage("Digite um e-mail valido no formato usuario@email.com.");
        return;
    }

    if (!password) {
        setLoginMessage("Digite sua senha para continuar.");
        return;
    }

    const loginBtn = loginForm.querySelector('button[type="submit"]');
    loginBtn.disabled = true;
    setLoginMessage("Verificando e-mail e senha no banco de dados...", false);

    const result = await loginWithApi(email, password);
    loginBtn.disabled = false;

    if (!result.ok) {
        setLoginMessage(result.message);
        return;
    }

    persistAuth(result.token, result.email, keepConnected, result.name);
    setLoginMessage(`Bem-vindo, ${result.name || result.email}!`, false);
    setTimeout(() => {
        openWindow("app", { email: result.email, name: result.name });
        loadRestaurants();
    }, WINDOW_TRANSITION_MS);
});

goRegisterBtn.addEventListener("click", () => {
    goToRegisterScreen();
});

backLoginBtn.addEventListener("click", () => {
    goToLoginScreen();
});

async function registerWithApi(name, email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, nome: name, email, password, senha: password })
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok) {
            return { ok: true, message: data.message || "Conta criada com sucesso." };
        }
        return { ok: false, message: data.error || "Nao foi possivel criar a conta." };
    } catch (_error) {
        return {
            ok: false,
            message: "Servidor offline. Execute iniciar.bat e aguarde o navegador abrir."
        };
    }
}

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setRegisterMessage("");

    if (!apiOnline && !(await refreshServerStatus())) {
        setRegisterMessage("Servidor offline. Execute iniciar.bat na pasta do projeto.");
        return;
    }

    const name = registerName.value.trim();
    const email = registerEmail.value.trim().toLowerCase();
    const password = registerPassword.value.trim();
    const confirm = registerConfirm.value.trim();
    const submitBtn = registerForm.querySelector('button[type="submit"]');

    if (!name) {
        setRegisterMessage("Informe seu nome para continuar.");
        return;
    }
    if (!EMAIL_REGEX.test(email)) {
        setRegisterMessage("Digite um e-mail valido no formato usuario@email.com.");
        return;
    }
    if (password.length < 6) {
        setRegisterMessage("A senha deve ter no minimo 6 caracteres.");
        return;
    }
    if (password !== confirm) {
        setRegisterMessage("As senhas nao conferem.");
        return;
    }

    const exists = await checkEmailExists(email);
    if (exists === true) {
        setRegisterMessage("Esse e-mail ja esta cadastrado no banco de dados.");
        return;
    }

    submitBtn.disabled = true;
    setRegisterMessage("Salvando no MySQL...", false);

    const result = await registerWithApi(name, email, password);
    submitBtn.disabled = false;

    if (!result.ok) {
        setRegisterMessage(result.message);
        return;
    }

    registerForm.reset();
    setRegisterMessage("Conta salva! Entrando automaticamente...", false);

    const loginResult = await loginWithApi(email, password);
    if (loginResult.ok) {
        persistAuth(loginResult.token, loginResult.email, false, loginResult.name);
        setTimeout(() => {
            openWindow("app", { email: loginResult.email, name: loginResult.name });
            loadRestaurants();
        }, WINDOW_TRANSITION_MS);
        return;
    }

    setRegisterMessage("Conta criada! Faca login com o mesmo e-mail e senha.", false);
    setTimeout(() => {
        goToLoginScreen({
            message: "Cadastro salvo no MySQL. Entre com o e-mail e senha que voce cadastrou.",
            isError: false,
            prefillEmail: email
        });
    }, WINDOW_TRANSITION_MS);
});

logoutBtn.addEventListener("click", () => {
    clearAuth();
    showLogin();
    loginForm.reset();
    setLoginMessage("");
});

aiForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!apiOnline && !(await refreshServerStatus())) {
        switchAppTab("assistant");
        aiResponse.innerHTML = `<p class="muted">Servidor offline. Execute iniciar.bat.</p>`;
        return;
    }

    const payload = {
        goal: document.getElementById("goal").value,
        preferences: document.getElementById("preferences").value.trim(),
        budget: Number(document.getElementById("budget").value),
        platform: document.getElementById("platform").value
    };

    if (!payload.budget || payload.budget < 10) {
        switchAppTab("assistant");
        aiResponse.innerHTML = `<p class="muted">Informe um orcamento de pelo menos R$ 10.</p>`;
        return;
    }

    const aiBtn = document.getElementById("ai-submit-btn");
    if (aiBtn) {
        aiBtn.disabled = true;
        aiBtn.textContent = "IA analisando...";
    }
    switchAppTab("assistant");
    aiResponse.classList.add("ai-box--empty");
    aiResponse.innerHTML = `<p class="muted">Aguarde...</p>`;

    try {
        const response = await fetch(`${API_BASE_URL}/recommendation`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
            aiResponse.innerHTML = `<p class="muted">${escapeHtml(data.error || "Nao foi possivel gerar a recomendacao.")}</p>`;
            return;
        }

        renderRecommendation(data);
    } catch (_error) {
        const local = localRecommendation(payload);
        if (!local) {
            aiResponse.innerHTML = `<p class="muted">Erro de conexao. Verifique se iniciar.bat esta rodando.</p>`;
            return;
        }

        const price = local.platform.price;
        const link99 = local.restaurant.food99?.url || "https://food.99app.com";
        const linkIfood = local.restaurant.ifood?.url || local.item.link || "https://www.ifood.com.br";
        renderRecommendation({
            dish: local.item.dish,
            restaurant: local.restaurant.name,
            rating: local.restaurant.rating,
            cuisine: local.restaurant.cuisine,
            price,
            platform: local.platform.name,
            protein: local.item.protein,
            calories: local.item.calories,
            deliveryTime: local.platform.delivery,
            link: local.platform.name === "99 Food" ? link99 : linkIfood,
            budgetWarning: price > payload.budget,
            usedAI: false,
            aiMessage: `Recomendo o ${local.item.dish} no ${local.restaurant.name}, por R$ ${price.toFixed(2)} no ${local.platform.name}, alinhado ao seu objetivo e orcamento.`
        });
    } finally {
        if (aiBtn) {
            aiBtn.disabled = false;
            aiBtn.textContent = "Recomendar";
        }
    }
});

sortBySelect?.addEventListener("change", renderRestaurants);
cuisineFilterSelect?.addEventListener("change", renderRestaurants);

if (compareSearchForm) {
    compareSearchForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        searchTerm = compareQueryInput?.value.trim() || "";
        await syncDeliveryPrices();
    });
}

compareQueryInput?.addEventListener("input", () => {
    searchTerm = compareQueryInput.value.trim();
    renderRestaurants();
});

loadRegisteredUsers();

const retryServerBtn = document.getElementById("retry-server-btn");
const offlineMessage = document.getElementById("offline-message");
if (retryServerBtn) {
    retryServerBtn.addEventListener("click", async () => {
        retryServerBtn.disabled = true;
        if (offlineMessage) {
            offlineMessage.textContent = "Conectando...";
            offlineMessage.classList.remove("ok");
        }
        apiOnline = await checkApiOnline();
        if (apiOnline) {
            window.location.replace(SITE_URL);
            return;
        }
        if (offlineMessage) {
            offlineMessage.textContent = "Servidor ainda parado. Execute iniciar.bat e aguarde.";
        }
        retryServerBtn.disabled = false;
    });
}

(async function initApp() {
    await refreshServerStatus();

    setInterval(async () => {
        if (!apiOnline) {
            apiOnline = await checkApiOnline();
        }
    }, 4000);

    const storedAuth = readStoredAuth();
    if (storedAuth && apiOnline) {
        showApp(storedAuth.email, storedAuth.name);
        loadRestaurants();
    } else if (apiOnline) {
        showLogin();
    }
})();
