/**
 * Dynamic Model Comparison Gallery
 * Renders detection results from JSON data for transparency
 */

class ComparisonGallery {
    constructor(containerId, dataUrl) {
        this.container = document.getElementById(containerId);
        this.dataUrl = dataUrl;
        this.data = null;
    }

    async load() {
        try {
            const response = await fetch(this.dataUrl);
            this.data = await response.json();
            this.render();
        } catch (error) {
            console.error('Failed to load comparison data:', error);
            this.renderError(error);
        }
    }

    render() {
        if (!this.data || !this.container) return;

        const html = `
            <div class="comparison-header">
                <div class="comparison-meta">
                    <span class="meta-item">Generated: ${this.formatDate(this.data.generated_at)}</span>
                    <span class="meta-item">Images: ${this.data.benchmark_config?.image_count || this.data.images?.length || 0}</span>
                    <span class="meta-item">Confidence ≥ ${(this.data.benchmark_config?.confidence_threshold * 100).toFixed(0)}%</span>
                </div>
                ${this.renderModelBadges()}
            </div>

            <div class="comparison-summary">
                ${this.renderSummary()}
            </div>

            <div class="comparison-grid">
                ${this.data.images.map(img => this.renderImageCard(img)).join('')}
            </div>
        `;

        this.container.innerHTML = html;
    }

    renderModelBadges() {
        const models = this.data.models || {};
        return `
            <div class="model-badges">
                ${Object.entries(models).map(([id, model]) => `
                    <span class="model-badge" style="background: ${model.color}20; border-color: ${model.color}; color: ${model.color}">
                        ${model.name}
                        ${model.is_current ? '<span class="badge-current">CURRENT</span>' : ''}
                        ${model.is_training ? '<span class="badge-training">TRAINING</span>' : ''}
                        ${model.mAP50 ? `<span class="badge-metric">mAP50: ${(model.mAP50 * 100).toFixed(3)}%</span>` : ''}
                    </span>
                `).join('')}
            </div>
        `;
    }

    renderSummary() {
        const summary = this.data.summary || {};
        const models = this.data.models || {};

        return `
            <table class="summary-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        ${Object.keys(models).map(id => `
                            <th style="color: ${models[id].color}">${models[id].name}</th>
                        `).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${this.getSummaryRows(summary, models)}
                    <tr class="total-row">
                        <td><strong>Total</strong></td>
                        ${Object.keys(models).map(id => `
                            <td><strong>${summary[id]?.total_detections || 0}</strong></td>
                        `).join('')}
                    </tr>
                </tbody>
            </table>
        `;
    }

    getSummaryRows(summary, models) {
        const categories = ['apparel', 'footwear', 'accessories', 'bags', 'people', 'vehicles', 'other'];
        const categoryLabels = {
            apparel: '👕 Apparel',
            footwear: '👟 Footwear',
            accessories: '🕶️ Accessories',
            bags: '🎒 Bags',
            people: '👤 People',
            vehicles: '🚗 Vehicles',
            other: '📦 Other'
        };

        return categories.map(cat => {
            const hasData = Object.values(summary).some(s => (s.by_category?.[cat] || 0) > 0);
            if (!hasData) return '';

            return `
                <tr>
                    <td>${categoryLabels[cat] || cat}</td>
                    ${Object.keys(models).map(id => {
                        const count = summary[id]?.by_category?.[cat] || 0;
                        const color = count > 0 ? models[id].color : 'var(--text-muted)';
                        return `<td style="color: ${color}">${count}</td>`;
                    }).join('')}
                </tr>
            `;
        }).join('');
    }

    renderImageCard(imageData) {
        const models = this.data.models || {};
        const modelIds = Object.keys(models);

        return `
            <div class="comparison-card">
                <div class="card-image">
                    <img src="images/${imageData.filename}" alt="${imageData.filename}" loading="lazy">
                </div>
                <div class="card-filename">${imageData.filename}</div>
                <div class="card-results">
                    ${modelIds.map(id => this.renderModelResult(id, imageData.results?.[id], models[id])).join('')}
                </div>
            </div>
        `;
    }

    renderModelResult(modelId, result, modelConfig) {
        if (!result) return '';

        const detections = result.detections || [];
        const topDetections = detections.slice(0, 5);  // Show top 5

        return `
            <div class="model-result" style="border-color: ${modelConfig?.color || '#888'}">
                <div class="result-header" style="background: ${modelConfig?.color || '#888'}20">
                    <span class="model-name" style="color: ${modelConfig?.color}">${modelConfig?.name || modelId}</span>
                    <span class="detection-count">${result.count} det</span>
                    <span class="timing">${result.processing_time_ms}ms</span>
                </div>
                <div class="result-detections">
                    ${topDetections.length === 0 ? '<span class="no-detections">No detections</span>' : ''}
                    ${topDetections.map(det => this.renderDetection(det, modelConfig?.color)).join('')}
                    ${detections.length > 5 ? `<span class="more-detections">+${detections.length - 5} more</span>` : ''}
                </div>
            </div>
        `;
    }

    renderDetection(detection, modelColor) {
        const categoryColors = {
            apparel: '#ef4444',
            footwear: '#f59e0b',
            accessories: '#8b5cf6',
            bags: '#06b6d4',
            people: '#10b981',
            vehicles: '#3b82f6',
            other: '#6b7280'
        };

        const bgColor = categoryColors[detection.category] || modelColor || '#6b7280';
        const confidence = (detection.confidence * 100).toFixed(1);

        return `
            <span class="detection-tag" style="background: ${bgColor}">
                ${detection.label} ${confidence}%
            </span>
        `;
    }

    renderError(error) {
        this.container.innerHTML = `
            <div class="comparison-error">
                <p>Failed to load comparison data</p>
                <code>${error.message}</code>
            </div>
        `;
    }

    formatDate(isoString) {
        try {
            return new Date(isoString).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return isoString;
        }
    }
}

// CSS styles for the comparison gallery
const comparisonStyles = `
<style>
.comparison-header {
    margin-bottom: 1.5rem;
}

.comparison-meta {
    display: flex;
    gap: 1rem;
    flex-wrap: wrap;
    margin-bottom: 1rem;
    font-size: 0.8rem;
    color: var(--text-muted);
}

.model-badges {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
}

.model-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.75rem;
    border-radius: 6px;
    border: 1px solid;
    font-size: 0.8rem;
    font-weight: 600;
}

.badge-current, .badge-training {
    font-size: 0.6rem;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
    background: currentColor;
    color: var(--bg-dark);
}

.badge-metric {
    font-size: 0.65rem;
    opacity: 0.8;
}

.summary-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1.5rem;
    font-size: 0.85rem;
}

.summary-table th,
.summary-table td {
    padding: 0.5rem 1rem;
    text-align: center;
    border-bottom: 1px solid var(--border-color);
}

.summary-table th:first-child,
.summary-table td:first-child {
    text-align: left;
}

.total-row {
    background: var(--bg-card);
}

.comparison-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 1.5rem;
}

.comparison-card {
    background: var(--bg-card);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid var(--border-color);
}

.card-image {
    aspect-ratio: 16/10;
    overflow: hidden;
}

.card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.card-filename {
    padding: 0.5rem 1rem;
    font-size: 0.75rem;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border-color);
}

.card-results {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 0.5rem;
    padding: 0.75rem;
}

.model-result {
    border: 1px solid;
    border-radius: 8px;
    overflow: hidden;
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.4rem 0.6rem;
    font-size: 0.7rem;
}

.model-name {
    font-weight: 600;
}

.detection-count, .timing {
    opacity: 0.7;
}

.result-detections {
    padding: 0.5rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.3rem;
}

.detection-tag {
    display: inline-block;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    font-size: 0.65rem;
    color: white;
}

.no-detections {
    color: var(--text-muted);
    font-size: 0.7rem;
    font-style: italic;
}

.more-detections {
    color: var(--text-muted);
    font-size: 0.65rem;
}

.comparison-error {
    text-align: center;
    padding: 2rem;
    color: var(--error);
}
</style>
`;

// Auto-inject styles
document.head.insertAdjacentHTML('beforeend', comparisonStyles);

// Export for use
window.ComparisonGallery = ComparisonGallery;
