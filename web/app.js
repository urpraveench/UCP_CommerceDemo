// UCP Demo Store - Frontend Application with API Call Viewer
const API_BASE_URL = 'http://localhost:8000';

// State management
let cart = [];
let currentCheckoutSession = null;
let apiCalls = [];
let selectedApiCall = null;

// AI Agent state management
let aiAgentCart = [];
let aiCheckoutSession = null;
let conversationHistory = [];
let isAIAgentMode = false;
let lastSearchedProducts = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadAllProducts();
    // Initialize in traditional mode
    switchShoppingMode('traditional');
});

function setupEventListeners() {
    // Profile discovery
    document.getElementById('load-profile').addEventListener('click', loadBusinessProfile);
    
    // Product search
    document.getElementById('search-btn').addEventListener('click', handleSearch);
    document.getElementById('product-search').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    document.getElementById('load-all-products').addEventListener('click', loadAllProducts);
    
    // Checkout
    document.getElementById('create-checkout').addEventListener('click', createCheckoutSession);
    document.getElementById('update-checkout').addEventListener('click', updateCheckoutSession);
    document.getElementById('complete-checkout').addEventListener('click', completeCheckout);
    
    // API Viewer controls
    document.getElementById('clear-api-calls').addEventListener('click', clearApiCalls);
    document.getElementById('toggle-api-viewer').addEventListener('click', toggleApiViewer);
    
    // AI Agent chat
    const aiChatInput = document.getElementById('ai-chat-input');
    const aiChatSend = document.getElementById('ai-chat-send');
    if (aiChatInput && aiChatSend) {
        aiChatSend.addEventListener('click', handleAIAgentMessage);
        aiChatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleAIAgentMessage();
            }
        });
    }
    
    // Keyboard support for modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('product-detail-modal');
            if (modal && modal.style.display === 'flex') {
                closeProductModal();
            }
        }
    });
}

// Enhanced API Logging
async function logAPICall(config) {
    const {
        method = 'GET',
        url,
        headers = {},
        body = null,
        description = ''
    } = config;
    
    const callId = generateUUID();
    const timestamp = new Date().toISOString();
    
    // Create API call object
    const apiCall = {
        id: callId,
        method: method.toUpperCase(),
        url: url.replace(API_BASE_URL, ''),
        fullUrl: url,
        headers: { ...headers },
        requestBody: body,
        status: 'pending',
        statusText: '',
        response: null,
        error: null,
        timestamp,
        description,
        duration: null
    };
    
    // Add to calls list
    apiCalls.unshift(apiCall); // Add to beginning
    updateApiViewer();
    
    try {
        const startTime = Date.now();
        
        const fetchOptions = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...headers
            }
        };
        
        if (body && method !== 'GET') {
            fetchOptions.body = JSON.stringify(body);
        }
        
        const response = await fetch(url, fetchOptions);
        const duration = Date.now() - startTime;
        
        let responseData;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
        } else {
            responseData = await response.text();
        }
        
        // Update API call with response
        apiCall.status = response.status;
        apiCall.statusText = response.statusText;
        apiCall.response = responseData;
        apiCall.duration = duration;
        
        updateApiViewer();
        return { response, data: responseData };
        
    } catch (error) {
        apiCall.status = 'error';
        apiCall.statusText = 'Network Error';
        apiCall.error = error.message;
        updateApiViewer();
        throw error;
    }
}

// API Viewer Functions
function updateApiViewer() {
    const listContainer = document.getElementById('api-calls-list');
    const countElement = document.getElementById('api-call-count');
    
    countElement.textContent = `${apiCalls.length} call${apiCalls.length !== 1 ? 's' : ''}`;
    
    if (apiCalls.length === 0) {
        listContainer.innerHTML = `
            <div class="api-call-placeholder">
                <p>API calls will appear here as you interact with the shopping UI</p>
            </div>
        `;
        return;
    }
    
    listContainer.innerHTML = apiCalls.map(call => {
        const statusClass = getStatusClass(call.status);
        const methodClass = getMethodClass(call.method);
        const isExpanded = selectedApiCall === call.id;
        
        return `
            <div class="api-call-item ${isExpanded ? 'expanded' : ''}" data-call-id="${call.id}">
                <div class="api-call-header" onclick="toggleApiCallDetails('${call.id}')">
                    <div class="api-call-method ${methodClass}">${call.method}</div>
                    <div class="api-call-url">${call.url}</div>
                    <div class="api-call-status ${statusClass}">
                        ${call.status === 'pending' ? '⏳' : call.status === 'error' ? '❌' : call.status}
                    </div>
                    <div class="api-call-toggle">${isExpanded ? '▼' : '▶'}</div>
                </div>
                ${isExpanded ? renderApiCallDetails(call) : ''}
            </div>
        `;
    }).join('');
    
    // Auto-scroll to top (latest call)
    if (apiCalls.length > 0) {
        listContainer.scrollTop = 0;
    }
}

function renderApiCallDetails(call) {
    const ucpHeaders = Object.keys(call.headers).filter(key => 
        key.toLowerCase().includes('ucp') || 
        key.toLowerCase().includes('request-signature') ||
        key.toLowerCase().includes('idempotency') ||
        key.toLowerCase().includes('request-id')
    );
    
    return `
        <div class="api-call-details">
            <div class="api-call-section">
                <div class="api-call-section-header">
                    <strong>Request</strong>
                    <button class="btn-copy" onclick="copyToClipboard('request-${call.id}')" title="Copy request">
                        📋 Copy
                    </button>
                </div>
                <div class="api-call-info">
                    <div><strong>URL:</strong> <code>${call.fullUrl}</code></div>
                    <div><strong>Method:</strong> <code>${call.method}</code></div>
                    ${call.duration ? `<div><strong>Duration:</strong> ${call.duration}ms</div>` : ''}
                </div>
                
                ${ucpHeaders.length > 0 ? `
                    <div class="ucp-headers">
                        <strong>🔷 UCP Headers:</strong>
                        <pre id="request-${call.id}" class="api-json">${JSON.stringify(
                            Object.fromEntries(ucpHeaders.map(h => [h, call.headers[h]])),
                            null, 2
                        )}</pre>
                    </div>
                ` : ''}
                
                ${Object.keys(call.headers).length > 0 ? `
                    <div class="api-call-subsection">
                        <strong>All Headers:</strong>
                        <pre class="api-json">${JSON.stringify(call.headers, null, 2)}</pre>
                    </div>
                ` : ''}
                
                ${call.requestBody ? `
                    <div class="api-call-subsection">
                        <strong>Request Body:</strong>
                        <pre class="api-json">${JSON.stringify(call.requestBody, null, 2)}</pre>
                    </div>
                ` : '<div class="api-call-subsection"><em>No request body</em></div>'}
            </div>
            
            <div class="api-call-section">
                <div class="api-call-section-header">
                    <strong>Response</strong>
                    <button class="btn-copy" onclick="copyToClipboard('response-${call.id}')" title="Copy response">
                        📋 Copy
                    </button>
                </div>
                <div class="api-call-info">
                    <div><strong>Status:</strong> <span class="${getStatusClass(call.status)}">${call.status} ${call.statusText}</span></div>
                </div>
                ${call.error ? `
                    <div class="api-error">
                        <strong>Error:</strong> ${call.error}
                    </div>
                ` : call.response ? `
                    <div class="api-call-subsection">
                        <strong>Response Body:</strong>
                        <pre id="response-${call.id}" class="api-json">${JSON.stringify(call.response, null, 2)}</pre>
                    </div>
                ` : '<div class="api-call-subsection"><em>No response yet...</em></div>'}
            </div>
        </div>
    `;
}

function toggleApiCallDetails(callId) {
    if (selectedApiCall === callId) {
        selectedApiCall = null;
    } else {
        selectedApiCall = callId;
    }
    updateApiViewer();
}

function clearApiCalls() {
    apiCalls = [];
    selectedApiCall = null;
    updateApiViewer();
}

function toggleApiViewer() {
    const panel = document.getElementById('api-viewer-panel');
    panel.classList.toggle('hidden');
}

function getStatusClass(status) {
    if (status === 'pending') return 'status-pending';
    if (status === 'error') return 'status-error';
    if (status >= 200 && status < 300) return 'status-success';
    if (status >= 400 && status < 500) return 'status-error';
    if (status >= 500) return 'status-error';
    return 'status-unknown';
}

function getMethodClass(method) {
    const classes = {
        'GET': 'method-get',
        'POST': 'method-post',
        'PUT': 'method-put',
        'DELETE': 'method-delete',
        'PATCH': 'method-patch'
    };
    return classes[method] || 'method-other';
}

function copyToClipboard(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        const text = element.textContent;
        navigator.clipboard.writeText(text).then(() => {
            // Show brief feedback
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = '✓ Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        });
    }
}

// Business Profile Discovery
async function loadBusinessProfile() {
    try {
        await logAPICall({
            method: 'GET',
            url: `${API_BASE_URL}/.well-known/ucp`,
            description: 'Discover business capabilities'
        });
        // Profile info is visible in API Call Viewer, no need to display separately
    } catch (error) {
        console.error('Error loading profile:', error);
        alert('Error loading business profile: ' + error.message);
    }
}

// Product Discovery
async function loadAllProducts() {
    try {
        const { data } = await logAPICall({
            method: 'GET',
            url: `${API_BASE_URL}/products`,
            description: 'Load all products'
        });
        
        displayProducts(data.products || []);
    } catch (error) {
        console.error('Error loading products:', error);
        alert('Error loading products: ' + error.message);
    }
}

async function handleSearch() {
    const query = document.getElementById('product-search').value.trim();
    try {
        const url = query 
            ? `${API_BASE_URL}/products?query=${encodeURIComponent(query)}`
            : `${API_BASE_URL}/products`;
        
        const { data } = await logAPICall({
            method: 'GET',
            url: url,
            description: query ? `Search products: "${query}"` : 'Load all products'
        });
        
        displayProducts(data.products || []);
    } catch (error) {
        console.error('Error searching products:', error);
        alert('Error searching products: ' + error.message);
    }
}

function displayProducts(products) {
    const grid = document.getElementById('products-grid');
    
    if (products.length === 0) {
        grid.innerHTML = '<div class="empty-state"><p>No products found</p></div>';
        return;
    }
    
    grid.innerHTML = products.map(product => {
        const rating = product.average_rating || 0;
        const ratingCount = product.rating_count || 0;
        const ratingStars = renderRatingStars(rating);
        
        // Extract delivery info from technical_info, default to "7-10 Days Delivery"
        const deliveryInfo = product.technical_info?.Delivery || "7-10 Days Delivery";
        
        return `
        <div class="product-card">
            <img src="${product.image_url || 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=400&fit=crop'}" 
                 alt="${product.title}"
                 onerror="this.src='https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=400&fit=crop'">
            <h3>${product.title}</h3>
            <p class="description">${product.description ? (product.description.length > 100 ? product.description.substring(0, 100) + '...' : product.description) : ''}</p>
            ${rating > 0 ? `
                <div class="product-rating">
                    ${ratingStars}
                    <span class="rating-value">${rating.toFixed(1)}</span>
                    <span class="rating-count">(${ratingCount})</span>
                </div>
            ` : ''}
            <div class="category">${product.category || 'General'}</div>
            <div class="delivery-info">
                <span class="delivery-icon">🚚</span>
                <span class="delivery-text">${deliveryInfo}</span>
            </div>
            <div class="price">$${(product.price / 100).toFixed(2)}</div>
            <div class="product-card-actions">
                <button class="btn btn-secondary" onclick="showProductDetails('${product.id}')">
                    View Details
                </button>
                <button class="btn btn-primary" onclick="addToCart('${product.id}', '${product.title}', ${product.price})">
                    Add to Cart
                </button>
            </div>
        </div>
    `;
    }).join('');
}

// Shopping Cart
function addToCart(productId, title, price) {
    const existingItem = cart.find(item => item.id === productId);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: productId,
            title: title,
            price: price,
            quantity: 1
        });
    }
    
    updateCartDisplay();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    updateCartDisplay();
}

function updateCartQuantity(productId, quantity) {
    const item = cart.find(item => item.id === productId);
    if (item) {
        if (quantity <= 0) {
            removeFromCart(productId);
        } else {
            item.quantity = quantity;
            updateCartDisplay();
        }
    }
}

function updateCartDisplay() {
    const cartItems = document.getElementById('cart-items');
    const cartTotals = document.getElementById('cart-totals');
    const createCheckoutBtn = document.getElementById('create-checkout');
    
    if (cart.length === 0) {
        cartItems.innerHTML = '<div class="empty-state"><p>Your cart is empty</p></div>';
        cartTotals.innerHTML = '';
        createCheckoutBtn.disabled = true;
        return;
    }
    
    // Display cart items
    cartItems.innerHTML = cart.map(item => {
        const subtotal = item.price * item.quantity;
        return `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.title}</h4>
                    <div class="quantity">Quantity: 
                        <button onclick="updateCartQuantity('${item.id}', ${item.quantity - 1})" 
                                style="padding: 2px 8px; margin: 0 5px;">-</button>
                        ${item.quantity}
                        <button onclick="updateCartQuantity('${item.id}', ${item.quantity + 1})" 
                                style="padding: 2px 8px; margin: 0 5px;">+</button>
                    </div>
                </div>
                <div class="cart-item-price">$${(subtotal / 100).toFixed(2)}</div>
                <button class="btn btn-secondary" onclick="removeFromCart('${item.id}')" 
                        style="padding: 8px 16px; margin-left: 10px;">Remove</button>
            </div>
        `;
    }).join('');
    
    // Calculate totals
    const subtotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const discount = currentCheckoutSession?.discounts?.applied?.reduce((sum, d) => sum + (typeof d === 'object' ? d.amount : 0), 0) || 0;
    const total = subtotal - discount;
    
    cartTotals.innerHTML = `
        <div class="total-line">
            <span>Subtotal:</span>
            <span>$${(subtotal / 100).toFixed(2)}</span>
        </div>
        ${discount > 0 ? `
            <div class="total-line">
                <span>Discount:</span>
                <span style="color: #28a745;">-$${(discount / 100).toFixed(2)}</span>
            </div>
        ` : ''}
        <div class="total-line final">
            <span>Total:</span>
            <span>$${(total / 100).toFixed(2)}</span>
        </div>
    `;
    
    createCheckoutBtn.disabled = false;
}

// Checkout Session Management
async function createCheckoutSession() {
    if (cart.length === 0) {
        alert('Cart is empty');
        return;
    }
    
    const buyerName = document.getElementById('buyer-name').value || 'John Doe';
    const buyerEmail = document.getElementById('buyer-email').value || 'john.doe@example.com';
    
    const lineItems = cart.map(item => ({
        item: {
            id: item.id,
            title: item.title,
            price: item.price
        },
        quantity: item.quantity
    }));
    
    const requestBody = {
        line_items: lineItems,
        currency: 'USD',
        buyer: {
            full_name: buyerName,
            email: buyerEmail
        }
    };
    
    try {
        const { data } = await logAPICall({
            method: 'POST',
            url: `${API_BASE_URL}/checkout-sessions`,
            headers: {
                'UCP-Agent': 'profile="https://agent.example/profile"',
                'request-signature': 'test',
                'idempotency-key': generateUUID(),
                'request-id': generateUUID()
            },
            body: requestBody,
            description: 'Create checkout session'
        });
        
        currentCheckoutSession = data;
        displayOutput('checkout-output', data);
        document.getElementById('checkout-section').style.display = 'block';
        
        // Scroll to checkout section
        document.getElementById('checkout-section').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error creating checkout:', error);
        alert('Error creating checkout session: ' + error.message);
    }
}

async function updateCheckoutSession() {
    if (!currentCheckoutSession) {
        alert('No checkout session. Please create one first.');
        return;
    }
    
    const discountCode = document.getElementById('discount-code').value.trim();
    if (!discountCode) {
        alert('Please enter a discount code');
        return;
    }
    
    const buyerName = document.getElementById('buyer-name').value || 'John Doe';
    const buyerEmail = document.getElementById('buyer-email').value || 'john.doe@example.com';
    
    const lineItems = cart.map(item => ({
        item: {
            id: item.id,
            title: item.title,
            price: item.price
        },
        quantity: item.quantity
    }));
    
    const requestBody = {
        id: currentCheckoutSession.id,
        line_items: lineItems,
        currency: 'USD',
        buyer: {
            full_name: buyerName,
            email: buyerEmail
        },
        discounts: {
            codes: [discountCode]
        }
    };
    
    try {
        const { data } = await logAPICall({
            method: 'PUT',
            url: `${API_BASE_URL}/checkout-sessions/${currentCheckoutSession.id}`,
            headers: {
                'UCP-Agent': 'profile="https://agent.example/profile"',
                'request-signature': 'test',
                'idempotency-key': generateUUID(),
                'request-id': generateUUID()
            },
            body: requestBody,
            description: `Apply discount: ${discountCode}`
        });
        
        currentCheckoutSession = data;
        displayOutput('checkout-output', data);
        updateCartDisplay();
    } catch (error) {
        console.error('Error updating checkout:', error);
        alert('Error updating checkout session: ' + error.message);
    }
}

async function completeCheckout() {
    if (!currentCheckoutSession) {
        alert('No checkout session. Please create one first.');
        return;
    }
    
    try {
        const { data } = await logAPICall({
            method: 'POST',
            url: `${API_BASE_URL}/checkout-sessions/${currentCheckoutSession.id}/complete`,
            description: 'Complete checkout'
        });
        
        currentCheckoutSession = data;
        displayOutput('checkout-output', data);
        
        alert('Checkout completed successfully! 🎉');
        
        // Reset cart
        cart = [];
        currentCheckoutSession = null;
        updateCartDisplay();
        document.getElementById('checkout-section').style.display = 'none';
    } catch (error) {
        console.error('Error completing checkout:', error);
        alert('Error completing checkout: ' + error.message);
    }
}

// Utility Functions
function displayOutput(elementId, data) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = JSON.stringify(data, null, 2);
    }
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Product Detail Modal Functions
async function showProductDetails(productId) {
    try {
        const { data } = await logAPICall({
            method: 'GET',
            url: `${API_BASE_URL}/products/${productId}`,
            description: `View product details: ${productId}`
        });
        
        const product = data.product || data;
        renderProductDetails(product);
        openProductModal();
    } catch (error) {
        console.error('Error loading product details:', error);
        alert('Error loading product details: ' + error.message);
    }
}

function renderProductDetails(product) {
    const modalContent = document.getElementById('product-detail-content');
    if (!modalContent) return;
    
    const rating = product.average_rating || 0;
    const ratingCount = product.rating_count || 0;
    const ratingStars = renderRatingStars(rating);
    
    modalContent.innerHTML = `
        <div class="product-detail-header">
            <div class="product-detail-image">
                <img src="${product.image_url || 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=400&fit=crop'}" 
                     alt="${product.title}"
                     onerror="this.src='https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=400&h=400&fit=crop'">
            </div>
            <div class="product-detail-info">
                <h2>${product.title}</h2>
                <div class="product-detail-price">$${(product.price / 100).toFixed(2)}</div>
                ${rating > 0 ? `
                    <div class="product-detail-rating">
                        ${ratingStars}
                        <span class="rating-value">${rating.toFixed(1)}</span>
                        <span class="rating-count">(${ratingCount} reviews)</span>
                    </div>
                ` : ''}
                <div class="product-detail-category">${product.category || 'General'}</div>
                <div class="product-detail-delivery">
                    <span class="delivery-icon">🚚</span>
                    <span class="delivery-text">${product.technical_info?.Delivery || "7-10 Days Delivery"}</span>
                </div>
                <button class="btn btn-primary btn-large" onclick="addToCart('${product.id}', '${product.title}', ${product.price}); closeProductModal();">
                    Add to Cart
                </button>
            </div>
        </div>
        
        <div class="product-detail-tabs">
            <button class="tab-btn active" onclick="switchProductTab('description')">Description</button>
            <button class="tab-btn" onclick="switchProductTab('technical')">Technical Info</button>
            <button class="tab-btn" onclick="switchProductTab('reviews')">Reviews (${ratingCount})</button>
        </div>
        
        <div class="product-detail-tab-content">
            <div id="tab-description" class="tab-pane active">
                <h3>Product Description</h3>
                <p>${product.description || 'No description available.'}</p>
            </div>
            
            <div id="tab-technical" class="tab-pane">
                <h3>Technical Specifications</h3>
                ${product.technical_info ? renderTechnicalInfo(product.technical_info) : '<p>No technical information available.</p>'}
            </div>
            
            <div id="tab-reviews" class="tab-pane">
                <h3>Customer Reviews</h3>
                ${product.comments && product.comments.length > 0 ? renderComments(product.comments) : '<p>No reviews yet.</p>'}
            </div>
        </div>
    `;
}

function renderRatingStars(rating) {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    let starsHTML = '';
    
    // Full stars
    for (let i = 0; i < fullStars; i++) {
        starsHTML += '<span class="star star-full">★</span>';
    }
    
    // Half star
    if (hasHalfStar) {
        starsHTML += '<span class="star star-half">★</span>';
    }
    
    // Empty stars
    for (let i = 0; i < emptyStars; i++) {
        starsHTML += '<span class="star star-empty">★</span>';
    }
    
    return `<div class="rating-stars">${starsHTML}</div>`;
}

function renderTechnicalInfo(techInfo) {
    if (!techInfo || typeof techInfo !== 'object') {
        return '<p>No technical information available.</p>';
    }
    
    let html = '<div class="technical-info">';
    
    // Handle nested objects
    if (techInfo.Specifications && typeof techInfo.Specifications === 'object') {
        html += '<table class="tech-spec-table">';
        for (const [key, value] of Object.entries(techInfo.Specifications)) {
            html += `
                <tr>
                    <td class="tech-spec-label">${key}</td>
                    <td class="tech-spec-value">${value}</td>
                </tr>
            `;
        }
        html += '</table>';
    } else {
        // Flat structure
        html += '<table class="tech-spec-table">';
        for (const [key, value] of Object.entries(techInfo)) {
            html += `
                <tr>
                    <td class="tech-spec-label">${key}</td>
                    <td class="tech-spec-value">${value}</td>
                </tr>
            `;
        }
        html += '</table>';
    }
    
    html += '</div>';
    return html;
}

function renderComments(comments) {
    if (!comments || comments.length === 0) {
        return '<p>No reviews yet.</p>';
    }
    
    // Sort by date (newest first)
    const sortedComments = [...comments].sort((a, b) => {
        return new Date(b.date) - new Date(a.date);
    });
    
    let html = '<div class="comments-list">';
    
    sortedComments.forEach(comment => {
        const ratingStars = renderRatingStars(comment.rating || 0);
        const verifiedBadge = comment.verified_purchase ? '<span class="verified-badge">✓ Verified Purchase</span>' : '';
        
        html += `
            <div class="comment-item">
                <div class="comment-header">
                    <div class="comment-author">
                        <strong>${comment.author || 'Anonymous'}</strong>
                        ${verifiedBadge}
                    </div>
                    <div class="comment-rating">
                        ${ratingStars}
                    </div>
                    <div class="comment-date">${comment.date || ''}</div>
                </div>
                <div class="comment-text">${comment.text || ''}</div>
            </div>
        `;
    });
    
    html += '</div>';
    return html;
}

function openProductModal() {
    const modal = document.getElementById('product-detail-modal');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }
}

function closeProductModal() {
    const modal = document.getElementById('product-detail-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = ''; // Restore scrolling
    }
}

function switchProductTab(tabName) {
    // Hide all tab panes
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab pane
    const selectedPane = document.getElementById(`tab-${tabName}`);
    if (selectedPane) {
        selectedPane.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// ============================================
// AI Agent Shopping Functions
// ============================================

// Switch between Traditional and AI Agent shopping modes
function switchShoppingMode(mode) {
    isAIAgentMode = (mode === 'ai-agent');
    
    const traditionalPanel = document.getElementById('traditional-shopping-panel');
    const aiAgentPanel = document.getElementById('ai-agent-shopping-panel');
    const traditionalTab = document.getElementById('tab-traditional');
    const aiAgentTab = document.getElementById('tab-ai-agent');
    
    if (mode === 'traditional') {
        traditionalPanel.style.display = 'block';
        aiAgentPanel.style.display = 'none';
        traditionalTab.classList.add('active');
        aiAgentTab.classList.remove('active');
    } else if (mode === 'ai-agent') {
        traditionalPanel.style.display = 'none';
        aiAgentPanel.style.display = 'block';
        traditionalTab.classList.remove('active');
        aiAgentTab.classList.add('active');
        
        // Initialize AI agent if not already done
        if (conversationHistory.length === 0) {
            initializeAIAgent();
        }
    }
}

// Initialize AI Agent with welcome message
async function initializeAIAgent() {
    conversationHistory = [];
    addAIChatMessage("Hello! I'm your AI shopping assistant powered by UCP (Universal Commerce Protocol) and advanced AI. I can help you discover products, add items to your cart, apply discounts, and complete your purchase - all through natural conversation!", 'agent');
    
    addAIChatMessage("Just tell me what you're looking for in natural language, and I'll help you find it! For example:", 'agent');
    addAIChatMessage("• 'Show me laptops'\n• 'I need a coffee maker'\n• 'Add the first one to my cart'\n• 'What's in my cart?'\n• 'Apply discount 10OFF'\n• 'Checkout'", 'agent');
    
    // Automatically discover business profile
    try {
        showAITypingIndicator();
        const { data } = await logAPICall({
            method: 'GET',
            url: `${API_BASE_URL}/.well-known/ucp`,
            description: 'AI Agent: Discover business profile'
        });
        hideAITypingIndicator();
        
        const capabilities = data.capabilities?.map(c => c.name).join(', ') || 'product discovery and checkout';
        addAIChatMessage(`Great! I've discovered the store's capabilities: ${capabilities}. I'm ready to help you shop!`, 'agent');
    } catch (error) {
        hideAITypingIndicator();
        addAIChatMessage("I've connected to the store. How can I help you today?", 'agent');
    }
}

// Handle AI Agent chat message
async function handleAIAgentMessage() {
    const input = document.getElementById('ai-chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message
    addAIChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showAITypingIndicator();
    
    // Process message with LLM backend
    await processAIAgentRequestWithLLM(message);
}

// Process AI Agent request with LLM backend
async function processAIAgentRequestWithLLM(message) {
    try {
        // Add user message to conversation history
        conversationHistory.push({
            role: 'user',
            content: message
        });
        
        // Call LLM backend
        const { data } = await logAPICall({
            method: 'POST',
            url: `${API_BASE_URL}/ai-agent/chat`,
            body: {
                message: message,
                conversation_history: conversationHistory,
                cart: aiAgentCart,
                checkout_session: aiCheckoutSession
            },
            description: 'AI Agent: Process chat message with LLM'
        });
        
        hideAITypingIndicator();
        
        // Update state from backend response
        if (data.cart) {
            aiAgentCart = data.cart;
        }
        if (data.checkout_session !== undefined) {
            aiCheckoutSession = data.checkout_session;
        }
        
        // Add assistant response to conversation history
        if (data.response) {
            conversationHistory.push({
                role: 'assistant',
                content: data.response
            });
            
            // Display response
            addAIChatMessage(data.response, 'agent');
            
            // If function calls were made that returned products, show them
            if (data.function_calls) {
                for (const funcCall of data.function_calls) {
                    if (funcCall.function === 'search_products' && funcCall.result?.data?.products) {
                        const products = funcCall.result.data.products;
                        lastSearchedProducts = products;
                        // Show product cards for search results
                        if (products.length > 0) {
                            displayProductsInChat(products.slice(0, 3));
                        }
                    }
                }
            }
        }
        
        // Update cart display
        updateAICartDisplay();
        
    } catch (error) {
        hideAITypingIndicator();
        console.error('Error processing AI agent request:', error);
        const errorMessage = error.response?.data?.detail || error.message || 'Unknown error';
        addAIChatMessage(`Sorry, I encountered an error: ${errorMessage}. Please check that your LLM API key is configured in the .env file (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.) and that LITELLM_MODEL is set.`, 'agent');
    }
}

// Add chat message to UI
function addAIChatMessage(text, type = 'agent') {
    const messagesContainer = document.getElementById('ai-chat-messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `ai-chat-message ${type}-message`;
    
    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="ai-chat-message-content">${escapeHtml(text)}</div>
            <div class="ai-chat-avatar">👤</div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="ai-chat-avatar">🤖</div>
            <div class="ai-chat-message-content">${formatAgentMessage(text)}</div>
        `;
    }
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Format agent message with markdown-like formatting
function formatAgentMessage(text) {
    // Escape HTML first
    let formatted = escapeHtml(text);
    // Convert **bold** to <strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Convert newlines to <br>
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted;
}

// Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Show typing indicator
function showAITypingIndicator() {
    const messagesContainer = document.getElementById('ai-chat-messages');
    if (!messagesContainer) return;
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'ai-chat-message agent-message ai-typing-indicator';
    typingDiv.id = 'ai-typing-indicator';
    typingDiv.innerHTML = `
        <div class="ai-chat-avatar">🤖</div>
        <div class="ai-chat-message-content">
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Hide typing indicator
function hideAITypingIndicator() {
    const indicator = document.getElementById('ai-typing-indicator');
    if (indicator) indicator.remove();
}

// Display products in chat
function displayProductsInChat(products) {
    const messagesContainer = document.getElementById('ai-chat-messages');
    if (!messagesContainer) return;
    
    const productsDiv = document.createElement('div');
    productsDiv.className = 'ai-chat-products';
    
    products.forEach(product => {
        const productCard = document.createElement('div');
        productCard.className = 'ai-chat-product-card';
        const rating = product.average_rating || 0;
        const ratingStars = renderRatingStars(rating);
        
        // Extract delivery info from technical_info, default to "7-10 Days Delivery"
        const deliveryInfo = product.technical_info?.Delivery || "7-10 Days Delivery";
        
        productCard.innerHTML = `
            <img src="${product.image_url || 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=200&h=200&fit=crop'}" 
                 alt="${product.title}"
                 onerror="this.src='https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=200&h=200&fit=crop'">
            <div class="ai-chat-product-info">
                <h4>${product.title}</h4>
                ${rating > 0 ? `<div class="ai-chat-product-rating">${ratingStars} ${rating.toFixed(1)}</div>` : ''}
                <div class="ai-chat-delivery-info">
                    <span class="delivery-icon">🚚</span>
                    <span class="delivery-text">${deliveryInfo}</span>
                </div>
                <div class="ai-chat-product-price">$${(product.price / 100).toFixed(2)}</div>
                <button class="btn btn-primary btn-sm" onclick="aiAgentAddToCart('${product.id}')">Add to Cart</button>
            </div>
        `;
        productsDiv.appendChild(productCard);
    });
    
    messagesContainer.appendChild(productsDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Add to cart from product card in chat
async function aiAgentAddToCart(productId) {
    // Find product
    let product = lastSearchedProducts.find(p => p.id === productId);
    if (!product) {
        try {
            const { data } = await logAPICall({
                method: 'GET',
                url: `${API_BASE_URL}/products/${productId}`,
                description: 'AI Agent: Get product for cart'
            });
            product = data.product || data;
        } catch (error) {
            addAIChatMessage("Sorry, I couldn't add that product. Please try again.", 'agent');
            return;
        }
    }
    
    const existingItem = aiAgentCart.find(item => item.id === productId);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        aiAgentCart.push({
            id: product.id,
            title: product.title,
            price: product.price,
            quantity: 1
        });
    }
    
    updateAICartDisplay();
    addAIChatMessage(`I've added "${product.title}" to your cart!`, 'agent');
}

// Update AI cart display
function updateAICartDisplay() {
    const cartSection = document.getElementById('ai-cart-section');
    const cartItems = document.getElementById('ai-cart-items');
    const cartTotals = document.getElementById('ai-cart-totals');
    
    if (!cartSection || !cartItems || !cartTotals) return;
    
    if (aiAgentCart.length === 0) {
        cartSection.style.display = 'none';
        return;
    }
    
    cartSection.style.display = 'block';
    
    cartItems.innerHTML = aiAgentCart.map(item => {
        const subtotal = item.price * item.quantity;
        return `
            <div class="cart-item">
                <div class="cart-item-info">
                    <h4>${item.title}</h4>
                    <div class="quantity">Quantity: ${item.quantity}</div>
                </div>
                <div class="cart-item-price">$${(subtotal / 100).toFixed(2)}</div>
            </div>
        `;
    }).join('');
    
    const subtotal = aiAgentCart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const discount = aiCheckoutSession?.discounts?.applied?.reduce((sum, d) => {
        return sum + (typeof d === 'object' ? (d.amount || 0) : 0);
    }, 0) || 0;
    const total = subtotal - discount;
    
    cartTotals.innerHTML = `
        ${discount > 0 ? `
            <div class="total-line">
                <span>Subtotal:</span>
                <span>$${(subtotal / 100).toFixed(2)}</span>
            </div>
            <div class="total-line">
                <span>Discount:</span>
                <span style="color: #28a745;">-$${(discount / 100).toFixed(2)}</span>
            </div>
        ` : ''}
        <div class="total-line final">
            <span>Total:</span>
            <span>$${(total / 100).toFixed(2)}</span>
        </div>
    `;
}

// Make functions globally available
window.toggleApiCallDetails = toggleApiCallDetails;
window.copyToClipboard = copyToClipboard;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateCartQuantity = updateCartQuantity;
window.showProductDetails = showProductDetails;
window.closeProductModal = closeProductModal;
window.switchProductTab = switchProductTab;
window.switchShoppingMode = switchShoppingMode;
window.aiAgentAddToCart = aiAgentAddToCart;
