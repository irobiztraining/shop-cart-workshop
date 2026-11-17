const productList = document.getElementById("product-list");
const cartLines = document.getElementById("cart-lines");
const emptyCart = document.getElementById("empty-cart");
const discountInput = document.getElementById("discount-input");
const discountStatus = document.getElementById("discount-status");
const errorMessage = document.getElementById("error-message");
let currentCart = null;
let busy = false;

class ApiError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

function formatTHB(satang) {
    const amount = BigInt(satang);
    const baht = (amount / 100n).toLocaleString("en-US");
    const fraction = (amount % 100n).toString().padStart(2, "0");
    return `฿${baht}.${fraction}`;
}

function createElement(tagName, text, testId) {
    const element = document.createElement(tagName);
    if (text !== undefined) {
        element.textContent = text;
    }
    if (testId !== undefined) {
        element.dataset.testid = testId;
    }
    return element;
}

function createButton(text, testId, label, onClick) {
    const button = createElement("button", text, testId);
    button.type = "button";
    button.setAttribute("aria-label", label);
    button.addEventListener("click", onClick);
    return button;
}

function setBusy(value) {
    busy = value;
    for (const id of ["product-controls", "cart-controls"]) {
        document.getElementById(id).disabled = busy || currentCart === null;
    }
}

function showError(error) {
    console.error(error);
    errorMessage.textContent = error.message;
    errorMessage.hidden = false;
}

function clearError() {
    errorMessage.textContent = "";
    errorMessage.hidden = true;
}

async function request(path, method = "GET", body) {
    let response;
    try {
        response = await fetch(path, {
            method,
            headers: body === undefined ? {} : { "Content-Type": "application/json" },
            body: body === undefined ? undefined : JSON.stringify(body),
        });
    } catch (error) {
        throw new Error("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ กรุณาลองใหม่", { cause: error });
    }

    let data;
    try {
        data = await response.json();
    } catch (error) {
        throw new Error("ไม่สามารถอ่านข้อมูลจากเซิร์ฟเวอร์ได้ กรุณาลองใหม่", { cause: error });
    }
    if (!response.ok) {
        throw new ApiError(
            response.status,
            typeof data.detail === "string" ? data.detail : "ไม่สามารถดำเนินการได้ กรุณาลองใหม่",
        );
    }
    return data;
}

function renderProducts(products) {
    productList.replaceChildren(...products.map((product) => {
        const card = createElement("article", undefined, `product-card-${product.id}`);
        card.className = "product-card";
        const name = createElement("h3", product.name);
        const price = createElement(
            "p", formatTHB(product.price_satang), `product-price-${product.id}`,
        );
        price.className = "product-price";
        const stock = createElement(
            "p", product.stock === 0 ? "สินค้าหมด" : `คงเหลือ ${product.stock} ชิ้น`,
        );
        stock.className = product.stock === 0 ? "stock sold-out" : "stock";
        const addButton = createButton(
            "เพิ่มลงตะกร้า",
            `add-to-cart-${product.id}`,
            `เพิ่ม ${product.name} ลงตะกร้า`,
            () => changeCart("/items", "POST", { product_id: product.id }),
        );
        addButton.disabled = product.stock === 0;
        card.append(name, price, stock, addButton);
        return card;
    }));
}

function renderCart(cart) {
    currentCart = cart;
    emptyCart.hidden = cart.items.length !== 0;
    cartLines.replaceChildren(...cart.items.map((item) => {
        const line = createElement("article", undefined, `cart-line-${item.product_id}`);
        line.className = "cart-line";
        const name = createElement("h3", item.name);
        const lineTotal = createElement(
            "p", formatTHB(item.line_total_satang), `line-total-${item.product_id}`,
        );
        lineTotal.className = "line-total";
        lineTotal.setAttribute("aria-label", `ราคารวม ${item.name}`);
        const controls = createElement("div");
        controls.className = "quantity-controls";
        const decrease = createButton(
            "−", `decrease-${item.product_id}`, `ลดจำนวน ${item.name}`,
            () => changeCart(`/items/${item.product_id}`, "PATCH", { qty: item.qty - 1 }),
        );
        decrease.disabled = item.qty === 1;
        const quantity = createElement("output", String(item.qty), `qty-${item.product_id}`);
        quantity.setAttribute("aria-label", `จำนวน ${item.name}`);
        const increase = createButton(
            "+", `increase-${item.product_id}`, `เพิ่มจำนวน ${item.name}`,
            () => changeCart(`/items/${item.product_id}`, "PATCH", { qty: item.qty + 1 }),
        );
        const remove = createButton(
            "ลบ", `remove-${item.product_id}`, `ลบ ${item.name}`,
            () => changeCart(`/items/${item.product_id}`, "DELETE"),
        );
        remove.className = "remove-button";
        controls.append(decrease, quantity, increase, remove);
        line.append(name, lineTotal, controls);
        return line;
    }));

    for (const field of ["subtotal", "discount", "shipping", "total"]) {
        document.querySelector(`[data-testid="cart-${field}"]`).textContent =
            formatTHB(cart[`${field}_satang`]);
    }
    discountInput.value = cart.discount_code ?? "";
    discountStatus.textContent = cart.discount_code ? `โค้ดที่ใช้อยู่: ${cart.discount_code}` : "";
    discountStatus.hidden = cart.discount_code === null;
}

async function changeCart(suffix, method, body) {
    if (busy) {
        return;
    }
    clearError();
    setBusy(true);
    try {
        const cart = await request(
            `/api/carts/${encodeURIComponent(currentCart.cart_id)}${suffix}`, method, body,
        );
        renderCart(cart);
    } catch (error) {
        showError(error);
    } finally {
        setBusy(false);
    }
}

async function loadCart() {
    const cartId = localStorage.getItem("cart_id");
    if (cartId) {
        try {
            return await request(`/api/carts/${encodeURIComponent(cartId)}`);
        } catch (error) {
            if (!(error instanceof ApiError) || error.status !== 404) {
                throw error;
            }
        }
    }
    return request("/api/carts", "POST");
}

async function initialize() {
    setBusy(true);
    try {
        renderProducts(await request("/api/products"));
        const cart = await loadCart();
        try {
            localStorage.setItem("cart_id", cart.cart_id);
        } catch (error) {
            throw new Error("ไม่สามารถบันทึกตะกร้าในเบราว์เซอร์ได้ กรุณาตรวจสอบการตั้งค่า", {
                cause: error,
            });
        }
        renderCart(cart);
    } catch (error) {
        showError(error);
    } finally {
        document.getElementById("loading-status").hidden = true;
        setBusy(false);
    }
}

document.getElementById("discount-form").addEventListener("submit", (event) => {
    event.preventDefault();
    changeCart("/discount", "PUT", { code: discountInput.value });
});

initialize();
