package com.xiaosi.nas.i18n;

import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/i18n")
@RequiredArgsConstructor
public class I18nController {

    private final I18nService i18nService;

    @GetMapping("/languages")
    public ResponseEntity<List<String>> getSupportedLanguages() {
        return ResponseEntity.ok(i18nService.getSupportedLanguages());
    }

    @GetMapping("/translations/{language}")
    public ResponseEntity<Map<String, String>> getTranslations(@PathVariable String language) {
        if (!i18nService.isLanguageSupported(language)) {
            language = i18nService.getDefaultLanguage();
        }
        return ResponseEntity.ok(Map.of(
            "language", language,
            "count", String.valueOf(i18nService.getSupportedLanguages().size())
        ));
    }

    @GetMapping("/translate")
    public ResponseEntity<Map<String, String>> translate(
        @RequestParam String key,
        @RequestParam(required = false) String language
    ) {
        if (language == null || !i18nService.isLanguageSupported(language)) {
            language = i18nService.getDefaultLanguage();
        }
        String translation = i18nService.translate(key, language);
        return ResponseEntity.ok(Map.of(
            "key", key,
            "language", language,
            "translation", translation
        ));
    }

    @GetMapping("/default-language")
    public ResponseEntity<Map<String, String>> getDefaultLanguage() {
        return ResponseEntity.ok(Map.of("language", i18nService.getDefaultLanguage()));
    }

    @PutMapping("/default-language")
    public ResponseEntity<Map<String, String>> setDefaultLanguage(@RequestParam String language) {
        if (i18nService.isLanguageSupported(language)) {
            i18nService.setDefaultLanguage(language);
            return ResponseEntity.ok(Map.of(
                "language", language,
                "message", "默认语言已更新"
            ));
        }
        return ResponseEntity.badRequest().body(Map.of(
            "error", "不支持的语言",
            "supported", i18nService.getSupportedLanguages().toString()
        ));
    }
}