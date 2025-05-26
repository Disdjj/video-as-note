// YouTube视频字幕转讲义工具 - 前端JavaScript

class VideoToNoteApp {
    constructor() {
        this.apiBase = '/api/v1';
        this.currentVideoId = null;
        this.pollInterval = null;

        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // 表单元素
        this.videoForm = document.getElementById('videoForm');
        this.videoIdInput = document.getElementById('videoId');
        this.modelInput = document.getElementById('modelName');
        this.languageSelect = document.getElementById('language');
        this.customLanguageInput = document.getElementById('customLanguage');
        this.submitBtn = document.getElementById('submitBtn');

        // 模型控制元素
        this.validateModelBtn = document.getElementById('validateModelBtn');
        this.modelStatus = document.getElementById('modelStatus');

        // 进度元素
        this.progressSection = document.getElementById('progressSection');
        this.progressMessage = document.getElementById('progressMessage');
        this.progressPercent = document.getElementById('progressPercent');
        this.progressBar = document.getElementById('progressBar');

        // 结果元素
        this.resultSection = document.getElementById('resultSection');
        this.lectureContent = document.getElementById('lectureContent');
        this.usedModel = document.getElementById('usedModel');
        this.createdTime = document.getElementById('createdTime');
        this.copyBtn = document.getElementById('copyBtn');
        this.downloadBtn = document.getElementById('downloadBtn');

        // 错误元素
        this.errorSection = document.getElementById('errorSection');
        this.errorMessage = document.getElementById('errorMessage');
    }

        bindEvents() {
        this.videoForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.copyBtn.addEventListener('click', () => this.copyToClipboard());
        this.downloadBtn.addEventListener('click', () => this.downloadMarkdown());

        // 模型验证事件
        this.validateModelBtn.addEventListener('click', () => this.validateModel());
        this.modelInput.addEventListener('input', () => this.resetModelStatus());

        // 语言选择事件
        this.languageSelect.addEventListener('change', () => this.handleLanguageChange());
    }

    async validateModel() {
        const modelName = this.modelInput.value.trim();
        if (!modelName) {
            this.updateModelStatus('请输入模型名称', 'error');
            return;
        }

        // 更新按钮状态
        this.validateModelBtn.disabled = true;
        this.validateModelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const response = await fetch(`${this.apiBase}/models/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model_name: modelName })
            });

            const result = await response.json();

            if (response.ok) {
                if (result.is_valid) {
                    this.updateModelStatus('✅ 模型验证成功，可以使用', 'success');
                } else {
                    this.updateModelStatus('❌ 模型不可用或配置不正确', 'error');
                }
            } else {
                this.updateModelStatus(`❌ 验证失败: ${result.detail}`, 'error');
            }
        } catch (error) {
            console.error('验证模型失败:', error);
            this.updateModelStatus('❌ 验证请求失败', 'error');
        } finally {
            // 恢复按钮状态
            this.validateModelBtn.disabled = false;
            this.validateModelBtn.innerHTML = '<i class="fas fa-check"></i>';
        }
    }

    resetModelStatus() {
        this.updateModelStatus('请输入LiteLLM支持的模型名称', 'default');
    }

    updateModelStatus(message, type = 'default') {
        if (!this.modelStatus) return;

        this.modelStatus.textContent = message;

        // 移除所有状态类
        this.modelStatus.classList.remove('text-gray-500', 'text-green-600', 'text-red-600');

        // 添加对应的状态类
        switch (type) {
            case 'success':
                this.modelStatus.classList.add('text-green-600');
                break;
            case 'error':
                this.modelStatus.classList.add('text-red-600');
                break;
            default:
                this.modelStatus.classList.add('text-gray-500');
        }
    }

    handleLanguageChange() {
        const selectedValue = this.languageSelect.value;

        if (selectedValue === 'custom') {
            // 显示自定义语言输入框
            this.customLanguageInput.classList.remove('hidden');
            this.customLanguageInput.required = true;
        } else {
            // 隐藏自定义语言输入框
            this.customLanguageInput.classList.add('hidden');
            this.customLanguageInput.required = false;
            this.customLanguageInput.value = '';
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const formData = new FormData(this.videoForm);

        // 处理语言参数
        let language = formData.get('language');
        if (language === 'custom') {
            const customLanguage = formData.get('customLanguage');
            if (!customLanguage || !customLanguage.trim()) {
                this.showError('请输入自定义语言名称');
                return;
            }
            language = customLanguage.trim();
        }

        const data = {
            video_id: formData.get('videoId'),
            model_name: formData.get('modelName'),
            language: language
        };

        if (!data.video_id || !data.model_name) {
            this.showError('请填写所有必需字段');
            return;
        }

        try {
            this.hideAllSections();
            this.setSubmitButtonState(true);

            // 提交处理请求
            const response = await fetch(`${this.apiBase}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.detail || '请求失败');
            }

            this.currentVideoId = result.video_id;
            this.showProgress();
            this.startPolling();

        } catch (error) {
            console.error('提交失败:', error);
            this.showError(error.message);
            this.setSubmitButtonState(false);
        }
    }

    startPolling() {
        this.pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`${this.apiBase}/status/${this.currentVideoId}`);
                const status = await response.json();

                this.updateProgress(status);

                if (status.status === 'completed') {
                    this.stopPolling();
                    this.showResult(status.result);
                } else if (status.status === 'error') {
                    this.stopPolling();
                    this.showError(status.message);
                }
            } catch (error) {
                console.error('轮询状态失败:', error);
                this.stopPolling();
                this.showError('获取处理状态失败');
            }
        }, 2000); // 每2秒轮询一次
    }

    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
        this.setSubmitButtonState(false);
    }

    updateProgress(status) {
        this.progressMessage.textContent = status.message;
        const progress = status.progress || 0;
        this.progressPercent.textContent = `${progress}%`;
        this.progressBar.style.width = `${progress}%`;
    }

    showProgress() {
        this.hideAllSections();
        this.progressSection.classList.remove('hidden');
        this.updateProgress({ message: '开始处理...', progress: 0 });
    }

    showResult(result) {
        this.hideAllSections();
        this.resultSection.classList.remove('hidden');

        // 渲染Markdown内容
        this.lectureContent.innerHTML = this.renderMarkdown(result.content);
        this.usedModel.textContent = result.model_used;
        this.createdTime.textContent = new Date(result.created_at).toLocaleString('zh-CN');

        // 存储结果用于复制和下载
        this.currentResult = result;
    }

    showError(message) {
        this.hideAllSections();
        this.errorSection.classList.remove('hidden');
        this.errorMessage.textContent = message;
        this.setSubmitButtonState(false);
    }

    hideAllSections() {
        this.progressSection.classList.add('hidden');
        this.resultSection.classList.add('hidden');
        this.errorSection.classList.add('hidden');
    }

    setSubmitButtonState(loading) {
        if (loading) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>处理中...';
            this.submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>开始生成讲义';
            this.submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }

    renderMarkdown(content) {
        // 简单的Markdown渲染（生产环境建议使用marked.js等库）
        let html = content
            // 标题
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // 引用块
            .replace(/^> (.*$)/gim, '<blockquote>$1</blockquote>')
            // 代码块
            .replace(/```mermaid\n([\s\S]*?)\n```/g, '<pre class="mermaid">$1</pre>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            // 行内代码
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // 粗体
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // 斜体
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // 链接
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" class="text-blue-600 hover:underline">$1</a>')
            // 列表
            .replace(/^\* (.*$)/gim, '<li>$1</li>')
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            // 换行
            .replace(/\n/g, '<br>');

        // 包装列表项
        html = html.replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');

        return html;
    }

    async copyToClipboard() {
        if (!this.currentResult) return;

        try {
            await navigator.clipboard.writeText(this.currentResult.content);
            this.showToast('内容已复制到剪贴板');
        } catch (error) {
            console.error('复制失败:', error);
            this.showToast('复制失败', 'error');
        }
    }

    downloadMarkdown() {
        if (!this.currentResult) return;

        const blob = new Blob([this.currentResult.content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentResult.title}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showToast('文件下载已开始');
    }

    showToast(message, type = 'success') {
        // 创建简单的toast通知
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg text-white z-50 ${
            type === 'error' ? 'bg-red-500' : 'bg-green-500'
        }`;
        toast.textContent = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new VideoToNoteApp();
});