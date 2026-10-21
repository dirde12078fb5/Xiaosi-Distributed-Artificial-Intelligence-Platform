/**
 * multipart/form-data 解析工具类
 * 用于处理文件推送接收
 */

class FormDataParser {
    /**
     * 解析multipart/form-data请求体
     * @param {Buffer} body - 请求体数据
     * @param {string} boundary - 分隔符
     * @returns {Object} 解析后的字段对象
     */
    static parse(body, boundary) {
        const result = {
            fields: {},
            files: []
        };

        if (!body || !boundary) {
            return result;
        }

        const boundaryBuffer = Buffer.from('--' + boundary);
        const parts = this.splitByBoundary(body, boundaryBuffer);

        for (const part of parts) {
            if (part.length === 0) continue;

            const headerEndIndex = this.findHeaderEnd(part);
            if (headerEndIndex === -1) continue;

            const headerPart = part.slice(0, headerEndIndex).toString();
            const contentPart = part.slice(headerEndIndex + 4); // skip \r\n\r\n

            // 移除末尾的\r\n
            let content = contentPart;
            if (content.length >= 2 && content[content.length - 2] === 0x0D && content[content.length - 1] === 0x0A) {
                content = content.slice(0, -2);
            }

            const disposition = this.parseContentDisposition(headerPart);

            if (disposition.filename) {
                // 文件字段
                result.files.push({
                    name: disposition.name,
                    filename: disposition.filename,
                    contentType: this.extractContentType(headerPart),
                    data: content
                });
            } else if (disposition.name) {
                // 普通字段
                result.fields[disposition.name] = content.toString();
            }
        }

        return result;
    }

    /**
     * 按分隔符分割Buffer
     */
    static splitByBoundary(buffer, boundary) {
        const parts = [];
        let start = 0;

        while (true) {
            const index = this.findIndex(buffer, boundary, start);
            if (index === -1) break;

            if (start > 0) {
                parts.push(buffer.slice(start, index));
            }

            start = index + boundary.length;

            // 跳过\r\n
            if (start < buffer.length && buffer[start] === 0x0D) {
                start += 2;
            }
        }

        return parts;
    }

    /**
     * 在Buffer中查找子Buffer的位置
     */
    static findIndex(buffer, search, fromIndex = 0) {
        for (let i = fromIndex; i <= buffer.length - search.length; i++) {
            let found = true;
            for (let j = 0; j < search.length; j++) {
                if (buffer[i + j] !== search[j]) {
                    found = false;
                    break;
                }
            }
            if (found) return i;
        }
        return -1;
    }

    /**
     * 找到header结束位置（\r\n\r\n）
     */
    static findHeaderEnd(buffer) {
        const pattern = Buffer.from('\r\n\r\n');
        return this.findIndex(buffer, pattern);
    }

    /**
     * 解析Content-Disposition头
     */
    static parseContentDisposition(header) {
        const result = {};

        const dispositionMatch = header.match(/Content-Disposition:\s*form-data;/i);
        if (!dispositionMatch) return result;

        // 提取name
        const nameMatch = header.match(/name="([^"]+)"/);
        if (nameMatch) {
            result.name = nameMatch[1];
        }

        // 提取filename
        const filenameMatch = header.match(/filename="([^"]+)"/);
        if (filenameMatch) {
            result.filename = filenameMatch[1];
        }

        return result;
    }

    /**
     * 提取Content-Type
     */
    static extractContentType(header) {
        const match = header.match(/Content-Type:\s*([^\r\n]+)/i);
        return match ? match[1].trim() : 'application/octet-stream';
    }
}

/**
 * 构建multipart/form-data请求体
 */
class FormDataBuilder {
    constructor() {
        this.boundary = '----XiaosiNAS' + Date.now() + Math.random().toString(36).substr(2);
        this.parts = [];
    }

    /**
     * 添加普通字段
     */
    addField(name, value) {
        this.parts.push({
            type: 'field',
            name: name,
            value: value
        });
        return this;
    }

    /**
     * 添加文件
     */
    addFile(name, filename, data, contentType = 'application/octet-stream') {
        this.parts.push({
            type: 'file',
            name: name,
            filename: filename,
            data: data,
            contentType: contentType
        });
        return this;
    }

    /**
     * 构建请求体
     */
    build() {
        const chunks = [];

        for (const part of this.parts) {
            chunks.push(Buffer.from(`--${this.boundary}\r\n`));

            if (part.type === 'field') {
                chunks.push(Buffer.from(`Content-Disposition: form-data; name="${part.name}"\r\n\r\n`));
                chunks.push(Buffer.from(part.value + '\r\n'));
            } else {
                chunks.push(Buffer.from(`Content-Disposition: form-data; name="${part.name}"; filename="${part.filename}"\r\n`));
                chunks.push(Buffer.from(`Content-Type: ${part.contentType}\r\n\r\n`));
                chunks.push(part.data);
                chunks.push(Buffer.from('\r\n'));
            }
        }

        chunks.push(Buffer.from(`--${this.boundary}--\r\n`));

        return Buffer.concat(chunks);
    }

    /**
     * 获取Content-Type头
     */
    getContentType() {
        return `multipart/form-data; boundary=${this.boundary}`;
    }
}

module.exports = {
    FormDataParser,
    FormDataBuilder
};