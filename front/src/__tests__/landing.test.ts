import { mount } from '@vue/test-utils';
import { afterEach, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import App from '../App.vue';
import { navItems } from '../content';

const flushPromises = () => new Promise((resolve) => window.setTimeout(resolve, 0));

describe('AI homework grading hero page', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders only the first-screen hero experience', () => {
    const wrapper = mount(App);
    const text = wrapper.text();

    expect(text).toContain('AI智能作业批改系统');
    expect(text).toContain('手写识别·智能评阅·错题归集·教学减负');
    expect(text).toContain('累计批改');
    expect(text).toContain('立即免费体验');

    expect(text).not.toContain('核心教学能力');
    expect(text).not.toContain('常见问题');
    expect(text).not.toContain('选择适配学校的方案');
    expect(wrapper.find('footer').exists()).toBe(false);
  });

  it('keeps top navigation visible but non-routing for now', () => {
    const wrapper = mount(App);
    const links = wrapper.findAll('.nav-links a');

    expect(navItems.map((item) => item.label)).toEqual([
      'AI批改',
      '模型优势',
      '教学场景',
      '资源中心',
      '版本方案'
    ]);
    expect(links).toHaveLength(5);
    expect(links.every((link) => link.attributes('href') === '#')).toBe(true);
  });

  it('navigates to the AI grading workspace when clicking AI批改', async () => {
    const wrapper = mount(App);
    const aiNav = wrapper.findAll('.nav-links a').find((link) => link.text() === 'AI批改');

    expect(aiNav).toBeTruthy();
    await aiNav!.trigger('click');
    await wrapper.vm.$nextTick();

    const text = wrapper.text();
    expect(text).toContain('AI智能批改工作台');
    expect(text).toContain('作业上传');
    expect(text).toContain('开始批改');
    expect(text).toContain('智能判分');
    expect(text).toContain('评语');
    expect(text).toContain('知识点薄弱分析');
    expect(text).toContain('教师复核');
    expect(text).toContain('OCR识别');
    expect(text).toContain('题目匹配');
    expect(text).not.toContain('OCR识别结果');
    expect(text).not.toContain('题目智能匹配');
    expect(text).not.toContain('AI初判结果');
    expect(text).not.toContain('面向中小学的 AI 批改基础设施');
  });

  it('accepts jpg/png homework images from the file picker and submits them to the backend', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      json: async () => ({ detail: 'Qwen-VL API Key 未配置' })
    });
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);
    const aiNav = wrapper.findAll('.nav-links a').find((link) => link.text() === 'AI批改');
    const file = new File(['image-bytes'], 'homework.png', { type: 'image/png' });

    await aiNav!.trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    });
    await input.trigger('change');
    await wrapper.find('.upload-dropzone button').trigger('click');
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('homework.png');
    expect(fetchMock).toHaveBeenCalledWith('/api/grading/analyze-homework', expect.objectContaining({
      method: 'POST',
      body: expect.any(FormData)
    }));
    expect(wrapper.text()).toContain('Qwen-VL API Key 未配置');
  });

  it('renders trusted_question grading and diagnosis results on the right panel', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: '前三阶段批改完成',
        subject: '数学',
        filename: 'homework.png',
        model: 'qwen-vl-max-latest',
        pipeline_version: 'perception-reasoning-diagnosis.v1',
        stages: {
          perception: {
            stage: 'perception',
            source: 'qwen-vl',
            trusted_question: {
              subject: '数学',
              question: '一袋面粉重 12 千克，已经用去 1/3，还剩多少千克？',
              student_answer: '12 × 2/3 = 8 千克',
              knowledge: ['分数乘法', '单位换算'],
              question_type: '计算题',
              confidence: 0.96
            }
          },
          grading: {
            stage: 'grading',
            routing: {
              skill: 'ReasoningSkill',
              reason: '过程计算题，优先校验中间步骤和结果单位'
            },
            score: 82,
            max_score: 100,
            judgement: '部分正确',
            process_score: 28,
            result_score: 54,
            comments: [
              {
                kind: 'concept',
                status: 'resolved',
                detail: '分数计算正确'
              }
            ]
          },
          diagnosis: {
            stage: 'diagnosis',
            error_causes: [
              {
                kind: 'expression_format_issue',
                evidence: '未写单位',
                severity: 'medium'
              }
            ],
            knowledge_points: ['分数乘法'],
            ability_tags: [
              {
                kind: 'process_expression',
                level: 'B'
              }
            ],
            student_profile_delta: {
              mastery: '提升'
            }
          }
        }
      })
    });
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);
    const file = new File(['image-bytes'], 'homework.png', { type: 'image/png' });

    await wrapper.findAll('.nav-links a')[0].trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    });
    await input.trigger('change');
    await wrapper.find('.upload-dropzone button').trigger('click');
    await flushPromises();
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('82');
    expect(wrapper.text()).toContain('部分正确');
    expect(wrapper.text()).toContain('ReasoningSkill');
    expect(wrapper.text()).toContain('一袋面粉重 12 千克');
    expect(wrapper.text()).toContain('未写单位');
    expect(wrapper.text()).toContain('process_expression');
    expect(wrapper.text()).toContain('mastery');
  });

  it('renders question stem and student answer in separate blocks', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: '前三阶段批改完成',
        subject: '数学',
        filename: 'equation.png',
        model: 'qwen3-vl-plus',
        pipeline_version: 'perception-reasoning-diagnosis.v1',
        stages: {
          perception: {
            stage: 'perception',
            source: 'qwen-vl',
            trusted_question: {
              subject: '数学',
              question: '(1) 15x+8x=45+1;',
              student_answer: '解：23x=46\nx=46÷23=2\nx=2',
              knowledge: ['一元一次方程', '合并同类项'],
              question_type: '计算题',
              confidence: 0.98
            }
          },
          grading: {
            stage: 'grading',
            routing: {
              skill: 'ReasoningSkill',
              reason: '纯方程求解'
            },
            score: 100,
            max_score: 100,
            judgement: 'correct',
            process_score: 50,
            result_score: 50,
            comments: []
          },
          diagnosis: {
            stage: 'diagnosis',
            error_causes: [],
            knowledge_points: ['一元一次方程'],
            ability_tags: [],
            student_profile_delta: {}
          }
        }
      })
    });
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);
    const file = new File(['image-bytes'], 'equation.png', { type: 'image/png' });

    await wrapper.findAll('.nav-links a')[0].trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    });
    await input.trigger('change');
    await wrapper.find('.upload-dropzone button').trigger('click');
    await flushPromises();
    await wrapper.vm.$nextTick();

    const questionBlocks = wrapper.findAll('.qa-block');
    expect(questionBlocks).toHaveLength(2);
    expect(questionBlocks[0].text()).toContain('(1) 15x+8x=45+1;');
    expect(questionBlocks[1].text()).toContain('解：23x=46');
    expect(questionBlocks[1].text()).toContain('x=46÷23=2');
  });

  it('shows a positive diagnosis card when the answer is correct', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: '前三阶段批改完成',
        subject: '数学',
        filename: 'equation.png',
        model: 'qwen3-vl-plus',
        pipeline_version: 'perception-reasoning-diagnosis.v1',
        stages: {
          perception: {
            stage: 'perception',
            source: 'qwen-vl',
            trusted_question: {
              subject: '数学',
              question: '15x + 8x = 45 + 1',
              student_answer: '23x = 46, x = 2',
              knowledge: ['一元一次方程', '合并同类项'],
              question_type: '计算题',
              confidence: 0.98
            }
          },
          grading: {
            stage: 'grading',
            routing: {
              skill: 'ReasoningSkill',
              reason: '纯方程求解'
            },
            score: 100,
            max_score: 100,
            judgement: 'correct',
            process_score: 46,
            result_score: 50,
            comments: []
          },
          diagnosis: {
            stage: 'diagnosis',
            error_causes: [],
            knowledge_points: ['一元一次方程'],
            ability_tags: [
              { kind: 'logical_reasoning', level: 'strong' }
            ],
            student_profile_delta: {}
          }
        }
      })
    });
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);
    const file = new File(['image-bytes'], 'equation.png', { type: 'image/png' });

    await wrapper.findAll('.nav-links a')[0].trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    });
    await input.trigger('change');
    await wrapper.find('.upload-dropzone button').trigger('click');
    await flushPromises();
    await wrapper.vm.$nextTick();

    const diagnosis = wrapper.find('.weakness-summary');
    expect(diagnosis.text()).toContain('继续加油');
    expect(diagnosis.text()).toContain('掌握知识点');
    expect(diagnosis.text()).not.toContain('错因');
  });

  it('shows error causes when the answer is wrong', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: '前三阶段批改完成',
        subject: '数学',
        filename: 'equation.png',
        model: 'qwen3-vl-plus',
        pipeline_version: 'perception-reasoning-diagnosis.v1',
        stages: {
          perception: {
            stage: 'perception',
            source: 'qwen-vl',
            trusted_question: {
              subject: '数学',
              question: '15x + 8x = 45 + 1',
              student_answer: '23x = 46, x = 3',
              knowledge: ['一元一次方程', '合并同类项'],
              question_type: '计算题',
              confidence: 0.98
            }
          },
          grading: {
            stage: 'grading',
            routing: {
              skill: 'ReasoningSkill',
              reason: '纯方程求解'
            },
            score: 80,
            max_score: 100,
            judgement: 'incorrect',
            process_score: 30,
            result_score: 50,
            comments: []
          },
          diagnosis: {
            stage: 'diagnosis',
            error_causes: [
              {
                kind: 'calculation_error',
                evidence: '最终解答与方程不符',
                severity: 'medium'
              }
            ],
            knowledge_points: ['一元一次方程'],
            ability_tags: [
              { kind: 'calculation_accuracy', level: 'weak' }
            ],
            student_profile_delta: {}
          }
        }
      })
    });
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);
    const file = new File(['image-bytes'], 'equation.png', { type: 'image/png' });

    await wrapper.findAll('.nav-links a')[0].trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    });
    await input.trigger('change');
    await wrapper.find('.upload-dropzone button').trigger('click');
    await flushPromises();
    await wrapper.vm.$nextTick();

    const diagnosis = wrapper.find('.weakness-summary');
    expect(diagnosis.text()).toContain('知识点薄弱分析');
    expect(diagnosis.text()).toContain('calculation_error');
    expect(diagnosis.text()).toContain('最终解答与方程不符');
  });
  it('lets users replace or remove the selected homework image', async () => {
    const wrapper = mount(App);
    const aiNav = wrapper.findAll('.nav-links a').find((link) => link.text() === 'AI批改');
    const firstFile = new File(['first-image'], 'first-homework.png', { type: 'image/png' });
    const secondFile = new File(['second-image'], 'second-homework.jpg', { type: 'image/jpeg' });

    await aiNav!.trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [firstFile],
      configurable: true
    });
    await input.trigger('change');

    expect(wrapper.text()).toContain('first-homework.png');

    await wrapper.find('.replace-file-button').trigger('click');
    Object.defineProperty(input.element, 'files', {
      value: [secondFile],
      configurable: true
    });
    await input.trigger('change');

    expect(wrapper.text()).not.toContain('first-homework.png');
    expect(wrapper.text()).toContain('second-homework.jpg');

    await wrapper.find('.remove-file-button').trigger('click');

    expect(wrapper.text()).not.toContain('second-homework.jpg');
    expect(wrapper.find('.upload-dropzone button').text()).toBe('选择文件');
  });

  it('accepts dragged jpg/png homework images', async () => {
    const wrapper = mount(App);
    const aiNav = wrapper.findAll('.nav-links a').find((link) => link.text() === 'AI批改');
    const file = new File(['image-bytes'], 'dragged-homework.jpg', { type: 'image/jpeg' });

    await aiNav!.trigger('click');
    await wrapper.find('.upload-dropzone').trigger('drop', {
      dataTransfer: { files: [file] }
    });
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('dragged-homework.jpg');
    expect(wrapper.text()).toContain('等待提交到 Qwen-VL 解析');
  });

  it('rejects non-image homework files before sending them to the backend', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);
    const aiNav = wrapper.findAll('.nav-links a').find((link) => link.text() === 'AI批改');
    const file = new File(['not-an-image'], 'homework.pdf', { type: 'application/pdf' });

    await aiNav!.trigger('click');
    const input = wrapper.find('input[type="file"]');
    Object.defineProperty(input.element, 'files', {
      value: [file],
      configurable: true
    });
    await input.trigger('change');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('仅支持 JPG、PNG 图片');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('opens student login after the free-trial button and does not show fake success state', async () => {
    const wrapper = mount(App);
    const headerButtons = wrapper.findAll('.header-actions a');

    expect(headerButtons.map((button) => button.text())).toEqual(['免费试用预约', '学生登录']);
    expect(wrapper.text()).not.toContain('学生端登录成功');
    expect(wrapper.find('.login-modal').exists()).toBe(false);

    await headerButtons[1].trigger('click');
    expect(wrapper.find('.login-modal').exists()).toBe(true);
    expect(wrapper.text()).toContain('学生端登录');
    expect(wrapper.text()).toContain('初始账号 student，密码 123');
  });

  it('shows a backend-not-started message when student login API is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('failed to fetch')));
    const wrapper = mount(App);

    await wrapper.findAll('.header-actions a')[1].trigger('click');
    await wrapper.find('input[name="username"]').setValue('student');
    await wrapper.find('input[name="password"]').setValue('123');
    await wrapper.find('form.login-card').trigger('submit');
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain('后端服务未启动');
    expect(wrapper.find('.login-modal').exists()).toBe(true);
    expect(wrapper.text()).not.toContain('学生端登录成功');
  });

  it('submits student login to the backend API and closes only after backend success', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ user: { username: 'student', role: 'student' } })
    });
    vi.stubGlobal('fetch', fetchMock);
    const wrapper = mount(App);

    await wrapper.findAll('.header-actions a')[1].trigger('click');
    await wrapper.find('input[name="username"]').setValue('student');
    await wrapper.find('input[name="password"]').setValue('123');
    await wrapper.find('form.login-card').trigger('submit');
    await wrapper.vm.$nextTick();

    expect(fetchMock).toHaveBeenCalledWith('/api/auth/student-login', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ username: 'student', password: '123' })
    }));
    expect(wrapper.find('.login-modal').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('学生端登录成功');
  });

  it('uses a native dashboard mock instead of nesting a full-page screenshot', () => {
    const wrapper = mount(App);

    expect(wrapper.find('img').exists()).toBe(false);
    expect(wrapper.find('.dashboard-preview').exists()).toBe(true);
    expect(wrapper.find('.app-topbar').exists()).toBe(true);
    expect(wrapper.find('.app-sidebar').exists()).toBe(true);
    expect(wrapper.find('.student-panel').exists()).toBe(true);
    expect(wrapper.find('.grading-paper').exists()).toBe(true);
    expect(wrapper.find('.analysis-column').exists()).toBe(true);
    expect(wrapper.text()).toContain('学生作业原图');
    expect(wrapper.text()).toContain('中国分数乘法应用题作业');
    expect(wrapper.text()).toContain('学情总览');
    expect(wrapper.text()).toContain('专题模板');
  });

  it('defines backend auth and student tables with the demo student seed', () => {
    const schema = readFileSync('../database/mysql/init/001_core_schema.sql', 'utf-8');

    expect(schema).toContain('CREATE TABLE IF NOT EXISTS auth_users');
    expect(schema).toContain('CREATE TABLE IF NOT EXISTS student_profiles');
    expect(schema).toContain('CREATE TABLE IF NOT EXISTS login_audit_logs');
    expect(schema).toContain('CREATE TABLE IF NOT EXISTS class_rooms');
    expect(schema).toContain("'student'");
    expect(schema).toContain("SHA2('123', 256)");
  });
});

