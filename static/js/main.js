document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 初始化所有模态框
    const modalElements = [].slice.call(document.querySelectorAll('.modal'));
    modalElements.map(function (modalEl) {
        return new bootstrap.Modal(modalEl);
    });
});