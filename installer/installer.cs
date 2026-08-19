using System;
using System.IO;
using System.IO.Compression;
using System.Diagnostics;
using System.Windows.Forms;
using System.Drawing;
using System.ComponentModel;

namespace NovaInstaller
{
    public class InstallerForm : Form
    {
        private Label titleLabel;
        private Label statusLabel;
        private ProgressBar progressBar;
        private Button installButton;
        private Button exitButton;
        private CheckBox desktopShortcut;
        private CheckBox startMenuShortcut;
        private CheckBox runOnStartup;
        private BackgroundWorker worker;

        private string installPath;
        private string exeName = "Nova.exe";

        public InstallerForm()
        {
            this.Text = "Nova Voice Assistant Setup";
            this.Size = new Size(500, 320);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Icon = System.Drawing.Icon.ExtractAssociatedIcon(Application.ExecutablePath);

            installPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Nova"
            );

            titleLabel = new Label
            {
                Text = "Nova Voice Assistant",
                Font = new Font("Segoe UI", 18, FontStyle.Bold),
                Location = new Point(20, 20),
                Size = new Size(460, 40),
                TextAlign = ContentAlignment.MiddleCenter,
            };

            statusLabel = new Label
            {
                Text = "Install Nova on your PC",
                Font = new Font("Segoe UI", 10),
                Location = new Point(20, 65),
                Size = new Size(460, 25),
                TextAlign = ContentAlignment.MiddleCenter,
            };

            desktopShortcut = new CheckBox
            {
                Text = "Create Desktop shortcut",
                Location = new Point(40, 105),
                Size = new Size(200, 25),
                Checked = true,
            };

            startMenuShortcut = new CheckBox
            {
                Text = "Add to Start Menu",
                Location = new Point(40, 130),
                Size = new Size(200, 25),
                Checked = true,
            };

            runOnStartup = new CheckBox
            {
                Text = "Run on Windows startup",
                Location = new Point(40, 155),
                Size = new Size(250, 25),
                Checked = false,
            };

            progressBar = new ProgressBar
            {
                Location = new Point(40, 195),
                Size = new Size(420, 25),
                Style = ProgressBarStyle.Marquee,
                Visible = false,
            };

            installButton = new Button
            {
                Text = "Install",
                Location = new Point(120, 235),
                Size = new Size(120, 35),
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(74, 158, 255),
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
            };
            installButton.Click += InstallClick;

            exitButton = new Button
            {
                Text = "Exit",
                Location = new Point(260, 235),
                Size = new Size(120, 35),
                FlatStyle = FlatStyle.Flat,
            };
            exitButton.Click += (s, e) => Application.Exit();

            this.Controls.AddRange(new Control[] {
                titleLabel, statusLabel, desktopShortcut, startMenuShortcut,
                runOnStartup, progressBar, installButton, exitButton
            });

            worker = new BackgroundWorker();
            worker.DoWork += DoInstall;
            worker.RunWorkerCompleted += InstallCompleted;
        }

        private void InstallClick(object sender, EventArgs e)
        {
            installButton.Enabled = false;
            exitButton.Enabled = false;
            desktopShortcut.Enabled = false;
            startMenuShortcut.Enabled = false;
            runOnStartup.Enabled = false;
            progressBar.Visible = true;
            progressBar.Style = ProgressBarStyle.Marquee;
            statusLabel.Text = "Installing...";
            worker.RunWorkerAsync();
        }

        private void DoInstall(object sender, DoWorkEventArgs e)
        {
            try
            {
                Directory.CreateDirectory(installPath);

                // Extract embedded Nova.exe
                string exePath = Path.Combine(installPath, exeName);
                using (var stream = System.Reflection.Assembly.GetExecutingAssembly()
                    .GetManifestResourceStream("Nova.exe"))
                {
                    if (stream == null)
                        throw new Exception("Embedded resource Nova.exe not found.");
                    using (var fs = new FileStream(exePath, FileMode.Create, FileAccess.Write))
                    {
                        stream.CopyTo(fs);
                    }
                }

                // Create shortcuts
                if (desktopShortcut.Checked)
                {
                    string desktopPath = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                    string shortcutPath = Path.Combine(desktopPath, "Nova.lnk");
                    CreateShortcut(exePath, shortcutPath);
                }

                if (startMenuShortcut.Checked)
                {
                    string startMenuPath = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.StartMenu),
                        "Programs", "Nova.lnk"
                    );
                    CreateShortcut(exePath, startMenuPath);
                }

                if (runOnStartup.Checked)
                {
                    string startupPath = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.Startup),
                        "Nova.lnk"
                    );
                    CreateShortcut(exePath, startupPath);
                }

                e.Result = "success";
            }
            catch (Exception ex)
            {
                e.Result = ex.Message;
            }
        }

        private void CreateShortcut(string targetPath, string shortcutPath)
        {
            try
            {
                Type t = Type.GetTypeFromCLSID(new Guid("72C24DD5-D70A-438B-8A42-98424B88AFB8"));
                dynamic shortcut = Activator.CreateInstance(t);
                shortcut.TargetPath = targetPath;
                shortcut.WorkingDirectory = Path.GetDirectoryName(targetPath);
                shortcut.Description = "Nova Voice Assistant";
                shortcut.Save(shortcutPath);
            }
            catch
            {
                // Fallback: copy a .url file
                string urlContent = "[InternetShortcut]\r\nURL=file:///" + targetPath.Replace('\\', '/') + "\r\n";
                System.IO.File.WriteAllText(shortcutPath.Replace(".lnk", ".url"), urlContent);
            }
        }

        private void InstallCompleted(object sender, RunWorkerCompletedEventArgs e)
        {
            progressBar.Visible = false;
            installButton.Enabled = true;
            exitButton.Enabled = true;

            string resultStr = (e.Result != null) ? e.Result.ToString() : null;
            if (resultStr == "success")
            {
                statusLabel.Text = "Nova has been installed successfully!";
                installButton.Text = "Run Nova";
                installButton.Click -= InstallClick;
                installButton.Click += (s, ev) =>
                {
                    string exePath = Path.Combine(installPath, exeName);
                    Process.Start(exePath);
                    Application.Exit();
                };
                MessageBox.Show(
                    "Nova has been installed successfully!\n\nPress Ctrl+Shift+T to start speaking.",
                    "Nova Installer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );
            }
            else
            {
                statusLabel.Text = "Installation failed.";
                string error = (e.Result != null) ? e.Result.ToString() : "Unknown error";
                MessageBox.Show(
                    "Installation failed:\n" + error,
                    "Nova Installer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                );
                installButton.Text = "Retry";
                installButton.Enabled = true;
                installButton.Click += InstallClick;
            }
        }

        [STAThread]
        public static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new InstallerForm());
        }
    }
}
