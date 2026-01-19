#!/usr/bin/env node

// BibTeX parser test script
// Run with: node test_bibtex_parser.js

const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

// BibTeX parser implementation
function parseBibTeX(bibtex) {
    try {
        const typeMatch = bibtex.match(/@(\w+)\s*\{([^,]+),/);
        if (!typeMatch) return null;

        const type = typeMatch[1];
        const key = typeMatch[2];
        const fields = {};

        const fieldsStart = bibtex.indexOf(',', bibtex.indexOf('{')) + 1;
        const fieldsSection = bibtex.substring(fieldsStart);
        
        // Advanced regex that properly handles nested braces
        // This pattern handles multiple levels of nesting by recursively matching brace pairs
        const fieldPattern = /(\w+)\s*=\s*\{((?:[^{}]|\{(?:[^{}]|\{[^}]*\})*\})*)\}/g;
        let match;
        
        while ((match = fieldPattern.exec(fieldsSection)) !== null) {
            const fieldName = match[1].toLowerCase();
            const fieldValue = match[2].trim();
            fields[fieldName] = fieldValue;
        }

        // Handle quoted strings as well
        const quotedFieldPattern = /(\w+)\s*=\s*"([^"]*)"/g;
        while ((match = quotedFieldPattern.exec(fieldsSection)) !== null) {
            const fieldName = match[1].toLowerCase();
            if (!fields[fieldName]) {
                fields[fieldName] = match[2].trim();
            }
        }

        return { type, key, fields };
    } catch (error) {
        console.error('Error parsing BibTeX:', error);
        return null;
    }
}

// Test cases
const testCases = [
    {
        name: "IEEE Journal with Double Braces",
        input: `@article{DBLP:journals/tkde/PanLWCWW24,
  journal = {{IEEE} Trans. Knowl. Data Eng.},
  title = {Test Paper},
  year = {2024}
}`,
        expectedJournal: '{IEEE} Trans. Knowl. Data Eng.'
    },
    {
        name: "ACM Journal with Protected Acronym",
        input: `@article{test2024,
  journal = {{ACM} Computing Surveys},
  year = {2024}
}`,
        expectedJournal: '{ACM} Computing Surveys'
    },
    {
        name: "Complex Conference Name",
        input: `@inproceedings{cvpr2024,
  booktitle = {Proceedings of the {IEEE/CVF} Conference on {Computer Vision}},
  year = {2024}
}`,
        expectedBooktitle: 'Proceedings of the {IEEE/CVF} Conference on {Computer Vision}'
    },
    {
        name: "Nature Journal with Double Protection",
        input: `@article{nature2025,
  journal = {{{Nature} Biotechnology}},
  year = {2025}
}`,
        expectedJournal: '{{Nature} Biotechnology}'
    },
    {
        name: "SIAM Journal",
        input: `@article{siam2024,
  journal = {{SIAM} J. Comput.},
  year = {2024}
}`,
        expectedJournal: '{SIAM} J. Comput.'
    },
    {
        name: "OpenAI as Protected Author",
        input: `@misc{openai2024,
  author = {{OpenAI}},
  title = {{GPT-4} Technical Report},
  year = {2024}
}`,
        expectedAuthor: '{OpenAI}',
        expectedTitle: '{GPT-4} Technical Report'
    }
];

// Run tests
console.log(`${colors.bright}${colors.blue}🧪 BibTeX Parser Test Suite${colors.reset}\n`);
console.log('=' .repeat(60));

let passCount = 0;
let failCount = 0;

testCases.forEach((test, index) => {
    console.log(`\n${colors.cyan}Test ${index + 1}: ${test.name}${colors.reset}`);
    console.log('-'.repeat(40));
    
    const result = parseBibTeX(test.input);
    
    if (!result) {
        console.log(`${colors.red}❌ Failed to parse BibTeX${colors.reset}`);
        failCount++;
        return;
    }
    
    let testPassed = true;
    
    // Check journal field if expected
    if (test.expectedJournal) {
        const actual = result.fields.journal;
        const expected = test.expectedJournal;
        
        console.log(`Journal field:`);
        console.log(`  Expected: "${expected}"`);
        console.log(`  Actual:   "${actual}"`);
        
        if (actual === expected) {
            console.log(`  ${colors.green}✅ Match!${colors.reset}`);
        } else {
            console.log(`  ${colors.red}❌ Mismatch!${colors.reset}`);
            testPassed = false;
        }
    }
    
    // Check booktitle field if expected
    if (test.expectedBooktitle) {
        const actual = result.fields.booktitle;
        const expected = test.expectedBooktitle;
        
        console.log(`Booktitle field:`);
        console.log(`  Expected: "${expected}"`);
        console.log(`  Actual:   "${actual}"`);
        
        if (actual === expected) {
            console.log(`  ${colors.green}✅ Match!${colors.reset}`);
        } else {
            console.log(`  ${colors.red}❌ Mismatch!${colors.reset}`);
            testPassed = false;
        }
    }
    
    // Check author field if expected
    if (test.expectedAuthor) {
        const actual = result.fields.author;
        const expected = test.expectedAuthor;
        
        console.log(`Author field:`);
        console.log(`  Expected: "${expected}"`);
        console.log(`  Actual:   "${actual}"`);
        
        if (actual === expected) {
            console.log(`  ${colors.green}✅ Match!${colors.reset}`);
        } else {
            console.log(`  ${colors.red}❌ Mismatch!${colors.reset}`);
            testPassed = false;
        }
    }
    
    // Check title field if expected
    if (test.expectedTitle) {
        const actual = result.fields.title;
        const expected = test.expectedTitle;
        
        console.log(`Title field:`);
        console.log(`  Expected: "${expected}"`);
        console.log(`  Actual:   "${actual}"`);
        
        if (actual === expected) {
            console.log(`  ${colors.green}✅ Match!${colors.reset}`);
        } else {
            console.log(`  ${colors.red}❌ Mismatch!${colors.reset}`);
            testPassed = false;
        }
    }
    
    if (testPassed) {
        console.log(`\n${colors.green}✅ Test Passed${colors.reset}`);
        passCount++;
    } else {
        console.log(`\n${colors.red}❌ Test Failed${colors.reset}`);
        failCount++;
    }
});

// Summary
console.log('\n' + '='.repeat(60));
console.log(`${colors.bright}Test Summary:${colors.reset}`);
console.log(`${colors.green}Passed: ${passCount}${colors.reset}`);
console.log(`${colors.red}Failed: ${failCount}${colors.reset}`);

const totalTests = testCases.length;
const passRate = ((passCount / totalTests) * 100).toFixed(1);

if (passCount === totalTests) {
    console.log(`\n${colors.bright}${colors.green}🎉 All tests passed! (${passRate}%)${colors.reset}`);
    process.exit(0);
} else {
    console.log(`\n${colors.bright}${colors.red}⚠️  Some tests failed (${passRate}% pass rate)${colors.reset}`);
    process.exit(1);
}