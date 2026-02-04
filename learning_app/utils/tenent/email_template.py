def otp_email_template(otp: str):
    return rf"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Email Verification</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f5f7; font-family:Arial, Helvetica, sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 0;">
        <table width="480" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          
          <!-- Logo -->
          <tr>
            <td align="center" style="padding:30px 20px 10px;">
              <img src="C:\Users\akhil\kasadra_backened_repo\learning_app\utils\tenent\dd-logo.jpg" width="48" alt="Company Logo" />
            </td>
          </tr>

          <!-- Company name -->
          <tr>
            <td align="center" style="padding-bottom:20px;">
              <h2 style="margin:0; color:#0052cc;">DigiDense Smart Learning </h2>
            </td>
          </tr>

          <tr>
            <td style="border-top:1px solid #e6e6e6;"></td>
          </tr>

          <!-- Content -->
          <tr>
            <td align="center" style="padding:30px 20px;">
              <p style="margin:0 0 15px; color:#333; font-size:16px;">
                Your verification code is:
              </p>

              <p style="
                font-size:32px;
                letter-spacing:6px;
                font-weight:bold;
                color:#000;
                margin:10px 0 20px;
              ">
                {otp}
              </p>

              <p style="margin:0; color:#666; font-size:14px;">
                If you didn’t try signing up, you can safely ignore this email.
              </p>
            </td>
          </tr>

          <tr>
            <td style="border-top:1px solid #e6e6e6;"></td>
          </tr>

          <!-- Footer -->
          <tr>
            <td align="center" style="padding:20px; font-size:12px; color:#999;">
              This message was sent by DigiDense Cloud
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""