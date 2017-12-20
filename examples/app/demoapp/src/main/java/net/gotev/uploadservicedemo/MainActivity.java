package net.gotev.uploadservicedemo;

import android.os.Bundle;
import android.view.View;
import android.widget.Button;

import net.gotev.uploadservice.UploadService;
import net.gotev.uploadservicedemo.issues.Issue251;

import butterknife.BindView;
import butterknife.OnClick;

public class MainActivity extends BaseActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        //runIssue.setVisibility(View.VISIBLE);
    }

    @OnClick(R.id.multipart_upload)
    public void onMultipartUpload(View view) {
        MultipartUploadActivity.show(this);
    }
}
