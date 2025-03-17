<!-- 모달 컴포넌트 (components/ConfirmModal.vue) -->
<template>
    <div class="modal-overlay" v-if="show" @click.self="close">
        <div class="modal-container">
            <div class="modal-header">
                <h3>{{ title }}</h3>
                <button class="close-button" @click="close">×</button>
            </div>
            <div class="modal-content">
                <p>{{ message }}</p>
            </div>
            <div class="modal-footer">
                <button class="cancel-button" @click="close">취소</button>
                <button class="confirm-button" @click="confirm">확인</button>
            </div>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ConfirmModal',
    props: {
        show: {
            type: Boolean,
            default: false
        },
        title: {
            type: String,
            default: '확인'
        },
        message: {
            type: String,
            default: '계속 진행하시겠습니까?'
        }
    },
    methods: {
        close() {
            this.$emit('close');
        },
        confirm() {
            this.$emit('confirm');
            this.close();
        }
    }
}
</script>

<style scoped>
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 100;
}

.modal-container {
    background-color: var(--card-color, white);
    border-radius: 8px;
    width: 90%;
    max-width: 400px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    animation: modal-appear 0.3s ease;
}

@keyframes modal-appear {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 15px 20px;
    border-bottom: 1px solid var(--border-color, #eee);
}

.modal-header h3 {
    margin: 0;
    font-size: 18px;
    color: var(--text-color, #333);
}

.close-button {
    background: none;
    border: none;
    font-size: 22px;
    cursor: pointer;
    color: var(--text-color, #333);
    opacity: 0.6;
    transition: opacity 0.2s;
}

.close-button:hover {
    opacity: 1;
}

.modal-content {
    padding: 20px;
}

.modal-content p {
    margin: 0;
    line-height: 1.5;
    color: var(--text-color, #333);
}

.modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    padding: 15px 20px;
    border-top: 1px solid var(--border-color, #eee);
}

.cancel-button,
.confirm-button {
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    border: none;
}

.cancel-button {
    background-color: var(--background-color, #f1f1f1);
    color: var(--text-color, #333);
}

.confirm-button {
    background-color: #ef4444;
    color: white;
}

.cancel-button:hover {
    background-color: var(--hover-color, #e5e5e5);
}

.confirm-button:hover {
    background-color: #dc2626;
}
</style>