<script setup lang="ts">
import { computed, ref } from 'vue';
import { heroMetrics, navItems } from './content';

type PageView = 'home' | 'grading';

type TrustedQuestion = {
  subject: string;
  question: string;
  student_answer: string;
  knowledge: string[];
  question_type: string;
  confidence: number;
};

type GradingComment = {
  kind: string;
  status: string;
  detail: string;
};

type GradingStage = {
  stage: string;
  routing: {
    skill: string;
    reason: string;
  };
  score: number;
  max_score: number;
  judgement: string;
  process_score: number | null;
  result_score: number | null;
  comments: GradingComment[];
};

type DiagnosisStage = {
  stage: string;
  error_causes: Array<{
    kind: string;
    evidence: string;
    severity: string;
  }>;
  knowledge_points: string[];
  ability_tags: Array<{
    kind: string;
    level: string;
  }>;
  student_profile_delta: Record<string, unknown>;
};

type HomeworkAnalysisStages = {
  perception: {
    stage: string;
    source: string;
    trusted_question: TrustedQuestion;
  };
  grading: GradingStage;
  diagnosis: DiagnosisStage;
};

type HomeworkAnalysisResponse = {
  message: string;
  subject: string;
  filename: string;
  model: string;
  pipeline_version: string;
  stages: HomeworkAnalysisStages;
};

const activeView = ref<PageView>('home');
const isLoginOpen = ref(false);
const loginError = ref('');
const isLoginSubmitting = ref(false);
const loginForm = ref({ username: 'student', password: '' });
const homeworkFileInput = ref<HTMLInputElement | null>(null);
const selectedHomeworkFile = ref<File | null>(null);
const uploadError = ref('');
const uploadStatus = ref('');
const isHomeworkAnalyzing = ref(false);
const homeworkAnalysisResult = ref<HomeworkAnalysisResponse | null>(null);

const homeworkStages = computed(() => homeworkAnalysisResult.value?.stages);

const isCorrectHomework = computed(() => {
  const grading = homeworkStages.value?.grading;
  if (!grading) return false;
  return grading.judgement === 'correct' || grading.score >= grading.max_score;
});

const positiveDiagnosisHighlights = () => {
  const knowledgePoints = homeworkStages.value?.diagnosis.knowledge_points ?? [];
  const abilityTags = homeworkStages.value?.diagnosis.ability_tags ?? [];
  const highlights: string[] = [];

  if (knowledgePoints.length) {
    highlights.push(`掌握知识点：${knowledgePoints.slice(0, 3).join('、')}`);
  }

  if (abilityTags.length) {
    highlights.push(
      `表现稳定：${abilityTags
        .slice(0, 3)
        .map((tag) => `${tag.kind} · ${tag.level}`)
        .join(' / ')}`
    );
  }

  if (!highlights.length) {
    highlights.push('本题思路清晰，继续保持。');
  }

  return highlights;
};

const diagnosticErrorCauses = () => {
  const causes = homeworkStages.value?.diagnosis.error_causes ?? [];
  if (causes.length) {
    return causes.map((item) => `${item.kind} / ${item.severity}：${item.evidence}`);
  }

  return [
    '过程表达：步骤可读性仍需提升',
    '知识点应用：需要加强题型识别',
    '结果书写：格式保持清晰'
  ];
};

const positiveDiagnosisSummary = () => {
  const question = homeworkStages.value?.perception.trusted_question.question || '';
  if (question.includes('=')) {
    return '本题思路清晰，方程变形和求解步骤基本完整，继续保持。';
  }
  return '本题作答准确，知识点掌握稳定，继续保持。';
};

const fallbackReasoningComment = () => {
  if (isCorrectHomework.value) return positiveDiagnosisSummary();
  return '解答中仍存在可优化点，建议结合下方错因逐步复核。';
};

const fallbackTeacherReview = () => {
  if (isCorrectHomework.value) return '本题完成较好，继续保持当前解题规范。';
  return '建议根据错因补充关键步骤，并复核最终结果。';
};

const diagnosisPanelTitle = computed(() => (isCorrectHomework.value ? '继续加油' : '知识点薄弱分析'));
const diagnosisPanelSubtitle = computed(() =>
  isCorrectHomework.value ? '本题正确，重点看稳定掌握与下一步巩固方向。' : '根据解答过程分析错因，定位需要强化的能力。'
);

const preventNavigation = (event: MouseEvent) => event.preventDefault();

const handleNavigation = (event: MouseEvent, label: string) => {
  preventNavigation(event);
  activeView.value = label === 'AI批改' ? 'grading' : 'home';
};

const openStudentLogin = (event: MouseEvent) => {
  preventNavigation(event);
  loginError.value = '';
  loginForm.value = { username: 'student', password: '' };
  isLoginOpen.value = true;
};

const closeStudentLogin = () => {
  isLoginOpen.value = false;
  loginError.value = '';
};

const isAllowedHomeworkImage = (file: File) => {
  const allowedTypes = ['image/jpeg', 'image/png'];
  return allowedTypes.includes(file.type) || /\.(jpe?g|png)$/i.test(file.name);
};

const selectHomeworkFile = (file?: File) => {
  uploadError.value = '';
  uploadStatus.value = '';
  homeworkAnalysisResult.value = null;

  if (!file) return;

  if (!isAllowedHomeworkImage(file)) {
    selectedHomeworkFile.value = null;
    uploadError.value = '仅支持 JPG、PNG 图片';
    return;
  }

  selectedHomeworkFile.value = file;
  uploadStatus.value = '等待提交到 Qwen-VL 解析';
};

const handleHomeworkFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  selectHomeworkFile(input.files?.[0]);
  input.value = '';
};

const handleHomeworkDrop = (event: DragEvent) => {
  selectHomeworkFile(event.dataTransfer?.files?.[0]);
};

const submitHomeworkImage = async () => {
  if (!selectedHomeworkFile.value || isHomeworkAnalyzing.value) return;

  uploadError.value = '';
  uploadStatus.value = '正在提交给后端解析...';
  isHomeworkAnalyzing.value = true;

  const formData = new FormData();
  formData.append('file', selectedHomeworkFile.value);
  formData.append('subject', '数学计算题');

  try {
    const response = await fetch('/api/grading/analyze-homework', { method: 'POST', body: formData });
    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      uploadError.value = payload.detail || payload.message || '作业解析失败';
      uploadStatus.value = '';
      homeworkAnalysisResult.value = null;
      return;
    }

    homeworkAnalysisResult.value = payload as HomeworkAnalysisResponse;
    uploadStatus.value = payload.message || 'Qwen-VL 解析任务已完成';
  } catch {
    uploadError.value = '后端批改服务未启动，请先运行 docker compose up -d mysql api';
    uploadStatus.value = '';
  } finally {
    isHomeworkAnalyzing.value = false;
  }
};

const handleUploadButtonClick = () => {
  if (selectedHomeworkFile.value) {
    void submitHomeworkImage();
    return;
  }
  homeworkFileInput.value?.click();
};

const replaceHomeworkFile = () => {
  uploadError.value = '';
  uploadStatus.value = '';
  homeworkAnalysisResult.value = null;
  homeworkFileInput.value?.click();
};

const removeHomeworkFile = () => {
  selectedHomeworkFile.value = null;
  uploadError.value = '';
  uploadStatus.value = '';
  homeworkAnalysisResult.value = null;
  if (homeworkFileInput.value) homeworkFileInput.value.value = '';
};

const submitStudentLogin = async () => {
  if (isLoginSubmitting.value) return;

  loginError.value = '';
  isLoginSubmitting.value = true;

  try {
    const response = await fetch('/api/auth/student-login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginForm.value)
    });

    if (!response.ok) {
      let message = '账号或密码不正确';
      try {
        const payload = await response.json();
        message = payload.detail || payload.message || message;
      } catch {
        // Keep default login error.
      }
      loginError.value = message;
      return;
    }

    closeStudentLogin();
  } catch {
    loginError.value = '后端服务未启动，请先运行 docker compose up -d mysql api';
  } finally {
    isLoginSubmitting.value = false;
  }
};
</script>

<template>
  <div class="page-shell">
    <header class="site-header">
      <a class="brand" href="#" aria-label="希沃智慧Pi 首页" @click="preventNavigation">
        <span class="brand-mark">S</span>
        <span>希沃智慧Pi</span>
      </a>

      <nav class="nav-links" aria-label="主导航">
        <a v-for="item in navItems" :key="item.label" href="#" @click="handleNavigation($event, item.label)">
          {{ item.label }}
        </a>
      </nav>

      <div class="header-actions">
        <label class="search-box" aria-label="搜索">
          <span>⌕</span>
          <input type="search" placeholder="搜索功能" />
        </label>
        <a class="pill-button primary" href="#" @click="preventNavigation">免费试用预约</a>
        <a class="pill-button secondary login-entry" href="#" @click="openStudentLogin">学生登录</a>
      </div>
    </header>

    <main v-if="activeView === 'home'" class="hero-stage">
      <section class="hero-section" aria-label="AI智能作业批改系统首屏">
        <div class="hero-copy">
          <p class="eyebrow">面向中小学的 AI 批改基础设施</p>
          <h1>AI智能作业批改系统</h1>
          <p class="hero-subtitle">手写识别·智能评阅·错题归集·教学减负</p>
          <p class="hero-description">
            帮助教师快速完成全学科作业批改，自动生成班级错题汇总与多维度学情分析，
            大幅压缩课后重复批改工作，让教师将更多精力投入备课、分层辅导等核心教学工作。
          </p>

          <div class="metric-grid" aria-label="核心数据背书">
            <article v-for="metric in heroMetrics" :key="metric.label" class="metric-card">
              <span>{{ metric.label }}</span>
              <strong>{{ metric.value }}</strong>
              <small>{{ metric.detail }}</small>
            </article>
          </div>

          <div class="hero-actions">
            <a class="pill-button primary large" href="#" @click="preventNavigation">立即免费体验</a>
            <a class="pill-button secondary large" href="#" @click="preventNavigation">查看操作演示</a>
          </div>
        </div>

        <div class="hero-visual" aria-label="系统操作页面预览">
          <div class="dashboard-preview">
            <div class="app-topbar">
              <div class="app-brand">
                <span class="app-logo"></span>
                <strong>Pi 教学</strong>
                <em>AI 智能作业批改</em>
              </div>
              <div class="app-actions"><span></span><span></span><span></span></div>
            </div>

            <div class="app-shell-body">
              <aside class="app-sidebar" aria-label="批改功能导航">
                <span class="active"></span><span></span><span></span><span></span><span></span><span></span><span></span>
              </aside>

              <div class="student-panel">
                <div class="panel-tabs"><span class="active">作业详情</span><span>批改记录</span></div>
                <div class="student-photo">
                  <div class="blackboard">A+B</div>
                  <div class="student s1"></div><div class="student s2"></div><div class="student s3"></div>
                </div>
                <div class="student-meta"><strong>学生作业原图</strong><button>重新识别</button></div>
                <div class="ocr-summary"><span>OCR 识别内容</span><p>共识别 6 道题，含 2 道过程题与 1 道表格题。</p></div>
                <div class="mini-lines"><span></span><span></span><span class="short"></span><span></span></div>
              </div>

              <main class="grading-paper">
                <div class="paper-toolbar"><span>中国分数乘法应用题作业</span><strong>自动批改中</strong></div>
                <div class="paper-question"><span>1.</span><p>一袋面粉重 12 千克，已经用去 1/3，还剩多少千克？</p></div>
                <div class="handwriting-area">
                  <div class="math-line long"></div><div class="math-line medium"></div><div class="math-line short"></div>
                  <i class="red-note note-one">步骤正确</i><i class="red-note note-two">单位需补充</i>
                </div>
                <div class="process-grid"><span></span><span></span><span></span><span></span><span></span><span></span></div>
                <div class="teacher-comment">AI 评语：解题思路清晰，最后一步建议写出“千克”。</div>
              </main>

              <aside class="analysis-column">
                <div class="analysis-header"><span class="active">批改</span><span>学情分析</span><span>错题集</span></div>
                <section class="learning-card">
                  <div class="card-title"><strong>学情总览</strong><span>92分</span></div>
                  <div class="answer-preview"><div class="answer-paper"></div><div class="red-marks"></div></div>
                </section>
                <section class="weakness-card app-card"><strong>专题建议</strong><div class="weakness-items"><span>单位换算</span><span>过程表达</span></div></section>
                <section class="template-strip app-card"><strong>专题模板</strong><div class="template-cards"><span class="orange"></span><span class="blue"></span><span class="green"></span></div></section>
              </aside>
            </div>
          </div>
        </div>
      </section>
    </main>

    <main v-if="activeView === 'grading'" class="ai-grading-page compact-grading-page" aria-label="AI智能批改工作台">
      <section class="grading-canvas">
        <div class="grading-canvas-header">
          <div>
            <p class="eyebrow">AI Grading Workspace</p>
            <h1>AI智能批改工作台</h1>
            <p>面向数学计算题、语文作文、英语作文等多学科作业，串联作业上传、OCR识别、题目匹配、智能判分、知识点薄弱分析与教师复核。</p>
          </div>
          <button class="grading-primary-action" type="button" :disabled="isHomeworkAnalyzing" @click="submitHomeworkImage">
            {{ isHomeworkAnalyzing ? '批改中...' : '开始批改' }}
          </button>
        </div>

        <div class="grading-main-grid">
          <section class="grading-upload-panel" aria-label="作业上传">
            <div class="panel-title-row"><span class="panel-kicker">01</span><h2>作业上传</h2></div>
            <input ref="homeworkFileInput" class="homework-file-input" type="file" accept=".jpg,.jpeg,.png,image/jpeg,image/png" @change="handleHomeworkFileChange" />
            <div class="upload-dropzone" @dragover.prevent @drop.prevent="handleHomeworkDrop">
              <strong>拖拽作业图片或扫描件</strong>
              <p>支持 JPG、PNG 图片；后续由 Qwen-VL 直接解析图片内容。</p>
              <div v-if="selectedHomeworkFile" class="selected-file">
                <span>{{ selectedHomeworkFile.name }}</span>
                <small>{{ uploadStatus || '等待提交到 Qwen-VL 解析' }}</small>
              </div>
              <p v-if="uploadError" class="upload-error">{{ uploadError }}</p>
              <div class="upload-actions">
                <button type="button" :disabled="isHomeworkAnalyzing" @click="handleUploadButtonClick">
                  {{ selectedHomeworkFile ? (isHomeworkAnalyzing ? '解析中...' : '上传解析') : '选择文件' }}
                </button>
                <button v-if="selectedHomeworkFile" class="replace-file-button" type="button" :disabled="isHomeworkAnalyzing" @click="replaceHomeworkFile">重新选择</button>
                <button v-if="selectedHomeworkFile" class="remove-file-button" type="button" :disabled="isHomeworkAnalyzing" @click="removeHomeworkFile">移除</button>
              </div>
            </div>
          </section>

          <section class="grading-score-panel">
            <span class="panel-kicker">02</span>
            <h2>智能判分</h2>
            <p v-if="homeworkStages">后端已返回判分结果，可直接查看题目理解、评分和诊断信息。</p>
            <p v-else>不仅判断对错，还能识别部分正确的解题过程并给出过程分。</p>

            <template v-if="homeworkStages">
              <div class="score-demo-card">
                <strong>{{ Math.round(homeworkStages.grading.score) }}</strong>
                <span>{{ homeworkStages.grading.judgement }} · {{ homeworkStages.grading.routing.skill }}</span>
              </div>
              <div class="result-summary">
                <div class="result-summary-row">
                  <span>满分 {{ homeworkStages.grading.max_score }}</span>
                  <span>过程 {{ homeworkStages.grading.process_score ?? 'N/A' }}</span>
                  <span>结果 {{ homeworkStages.grading.result_score ?? 'N/A' }}</span>
                </div>
                <p class="result-summary-text">{{ homeworkStages.grading.routing.reason }}</p>
              </div>
            </template>

            <div v-else class="score-demo-card"><strong>92</strong><span>过程完整度高，单位表达需补充</span></div>
          </section>

          <section class="grading-feedback-panel">
            <div v-if="homeworkStages" class="feedback-box">
              <h2>题目理解</h2>
              <p><strong>学科：</strong>{{ homeworkStages.perception.trusted_question.subject }}</p>
              <p><strong>题型：</strong>{{ homeworkStages.perception.trusted_question.question_type }}</p>
              <p><strong>置信度：</strong>{{ homeworkStages.perception.trusted_question.confidence }}</p>
              <div class="qa-block">
                <span>题干</span>
                <pre>{{ homeworkStages.perception.trusted_question.question }}</pre>
              </div>
              <div class="qa-block">
                <span>学生作答</span>
                <pre>{{ homeworkStages.perception.trusted_question.student_answer }}</pre>
              </div>
              <p><strong>知识点：</strong>{{ homeworkStages.perception.trusted_question.knowledge.join('、') || '暂无' }}</p>
            </div>

            <div class="feedback-box">
              <h2>评语</h2>
              <ul v-if="homeworkStages && homeworkStages.grading.comments.length" class="structured-list">
                <li v-for="comment in homeworkStages.grading.comments" :key="`${comment.kind}-${comment.detail}`">
                  <strong>{{ comment.kind }}</strong> / {{ comment.status }}：{{ comment.detail }}
                </li>
              </ul>
              <p v-else>{{ fallbackReasoningComment() }}</p>
            </div>

            <div class="feedback-box weakness-summary" :class="{ positive: isCorrectHomework }">
              <h2>{{ diagnosisPanelTitle }}</h2>
              <p class="diagnosis-lead">{{ diagnosisPanelSubtitle }}</p>

              <template v-if="isCorrectHomework">
                <ul class="structured-list">
                  <li v-for="item in positiveDiagnosisHighlights()" :key="item">{{ item }}</li>
                </ul>
              </template>

              <template v-else>
                <ul class="structured-list">
                  <li v-for="item in diagnosticErrorCauses()" :key="item">{{ item }}</li>
                </ul>
              </template>

              <div v-if="homeworkStages && homeworkStages.diagnosis.ability_tags.length" class="tag-cloud">
                <span v-for="tag in homeworkStages.diagnosis.ability_tags" :key="`${tag.kind}-${tag.level}`">{{ tag.kind }} · {{ tag.level }}</span>
              </div>
            </div>

            <div class="feedback-box review-box">
              <h2>教师复核</h2>
              <pre v-if="homeworkStages" class="delta-preview">{{ JSON.stringify(homeworkStages.diagnosis.student_profile_delta, null, 2) }}</pre>
              <textarea v-else aria-label="教师复核评语">{{ fallbackTeacherReview() }}</textarea>
            </div>
          </section>
        </div>

        <div class="grading-flow-strip" aria-label="批改流程">
          <span>作业上传</span><span>OCR识别</span><span>题目匹配</span><span>AI初判</span><span>教师复核</span>
        </div>
      </section>
    </main>

    <div v-if="isLoginOpen" class="login-modal" role="dialog" aria-modal="true" aria-labelledby="student-login-title">
      <form class="login-card" @submit.prevent="submitStudentLogin">
        <button class="login-close" type="button" aria-label="关闭登录弹窗" @click="closeStudentLogin">×</button>
        <p class="login-eyebrow">Student Portal</p>
        <h2 id="student-login-title">学生端登录</h2>
        <p class="login-hint">初始账号 student，密码 123</p>
        <label><span>账号</span><input v-model="loginForm.username" name="username" autocomplete="username" /></label>
        <label><span>密码</span><input v-model="loginForm.password" name="password" type="password" autocomplete="current-password" /></label>
        <p v-if="loginError" class="login-error">{{ loginError }}</p>
        <button class="login-submit" type="submit" :disabled="isLoginSubmitting">{{ isLoginSubmitting ? '登录中...' : '进入学生端' }}</button>
      </form>
    </div>
  </div>
</template>

