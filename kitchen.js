// Cargar órdenes al iniciar
document.addEventListener('DOMContentLoaded', function() {
    loadOrders();
    // Actualizar cada 5 segundos
    setInterval(loadOrders, 5000);
});

function loadOrders() {
    fetch('/api/orders')
        .then(response => response.json())
        .then(data => {
            displayOrders(data.orders);
        })
        .catch(error => {
            console.error('Error loading orders:', error);
        });
}

function displayOrders(orders) {
    const pendingContainer = document.getElementById('pending-orders');
    const preparingContainer = document.getElementById('preparing-orders');
    const readyContainer = document.getElementById('ready-orders');
    
    // Limpiar contenedores
    pendingContainer.innerHTML = '';
    preparingContainer.innerHTML = '';
    readyContainer.innerHTML = '';
    
    // Agrupar órdenes por estado
    const pendingOrders = orders.filter(order => order.status === 'pending');
    const preparingOrders = orders.filter(order => order.status === 'preparing');
    const readyOrders = orders.filter(order => order.status === 'ready');
    
    // Mostrar órdenes pendientes
    if (pendingOrders.length === 0) {
        pendingContainer.innerHTML = '<div class="empty-state">No pending orders</div>';
    } else {
        pendingOrders.forEach(order => {
            pendingContainer.appendChild(createOrderCard(order));
        });
    }
    
    // Mostrar órdenes en preparación
    if (preparingOrders.length === 0) {
        preparingContainer.innerHTML = '<div class="empty-state">No orders being prepared</div>';
    } else {
        preparingOrders.forEach(order => {
            preparingContainer.appendChild(createOrderCard(order));
        });
    }
    
    // Mostrar órdenes listas
    if (readyOrders.length === 0) {
        readyContainer.innerHTML = '<div class="empty-state">No orders ready</div>';
    } else {
        readyOrders.forEach(order => {
            readyContainer.appendChild(createOrderCard(order));
        });
    }
}

function createOrderCard(order) {
    const card = document.createElement('div');
    card.className = `order-card ${order.status}`;
    
    const orderDetails = JSON.parse(order.order_details);
    const time = new Date(order.created_at).toLocaleTimeString();
    
    card.innerHTML = `
        <div class="order-header">
            <div class="order-number">Order #${order.id}</div>
            <div class="order-time">${time}</div>
        </div>
        <div class="order-details">
            <div class="order-item">
                <span class="item-name">${order.pizza} (${order.size})</span>
                <span class="item-price">$${orderDetails.pizza_price || 0}</span>
            </div>
            ${order.drink ? `
            <div class="order-item">
                <span class="item-name">${order.drink}</span>
                <span class="item-price">$${orderDetails.drink_price || 0}</span>
            </div>
            ` : ''}
        </div>
        <div class="order-total">Total: $${order.total}</div>
        <div class="order-actions">
            ${getActionButtons(order)}
        </div>
    `;
    
    // Agregar event listeners a los botones
    const buttons = card.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.dataset.action;
            const orderId = order.id;
            updateOrderStatus(orderId, action);
        });
    });
    
    return card;
}

function getActionButtons(order) {
    switch(order.status) {
        case 'pending':
            return `<button class="btn btn-primary" data-action="preparing">Start Preparing</button>`;
        case 'preparing':
            return `<button class="btn btn-success" data-action="ready">Mark Ready</button>`;
        case 'ready':
            return `<button class="btn btn-warning" data-action="completed">Complete</button>`;
        default:
            return '';
    }
}

function updateOrderStatus(orderId, action) {
    const statusMap = {
        'preparing': 'preparing',
        'ready': 'ready',
        'completed': 'completed'
    };
    
    fetch(`/api/orders/${orderId}/status`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: statusMap[action] })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadOrders(); // Recargar órdenes
        } else {
            alert('Error updating order status');
        }
    })
    .catch(error => {
        console.error('Error updating order:', error);
        alert('Error updating order status');
    });
} 